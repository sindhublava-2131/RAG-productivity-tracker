from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import auth
import models
from core.config import settings
from core.logging import configure_logging
from database import Base, SessionLocal, engine
from routes import analytics_routes, auth_routes, health_routes, rag_routes, task_routes
from services.rag.memory import MemoryIngestionError, format_task_memory
from services.rag.service import get_rag_service

configure_logging()
logger = logging.getLogger("cozy.main")

BACKEND_DIR = Path(__file__).parent.resolve()


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _run_migrations(fail_fast: bool = False) -> None:
    """Apply Alembic migrations to the configured database.

    When ``fail_fast`` is False (development), a legacy database created with
    ``create_all`` (no ``alembic_version`` table) falls back to metadata
    creation so existing dev data is never lost.
    """
    try:
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        command.upgrade(cfg, "head")
        logger.info("Database schema is up to date (Alembic).")
    except Exception as exc:
        if fail_fast:
            logger.error("Alembic migration failed in production: %s", exc)
            raise
        logger.warning(
            "Alembic migration failed (%s); falling back to metadata create_all for dev.",
            exc,
        )
        Base.metadata.create_all(bind=engine)


def _seed_demo_data() -> None:
    """Create a demo user/tasks/memories (development only)."""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == "demo@cozy.app").first()
        if user:
            return

        user = models.User(
            name="Cozy User 🌸",
            email="demo@cozy.app",
            password_hash=auth.get_password_hash("cozy123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        now = _utcnow()
        seed_tasks = [
            {
                "title": "Complete React Component Architecture Assignment",
                "description": "Build modular TypeScript components with Tailwind styling",
                "priority": "HIGH",
                "status": "COMPLETED",
                "due_date": now - timedelta(hours=5),
                "completed_at": now - timedelta(hours=2),
                "estimated_minutes": 60,
                "actual_minutes": 45,
            },
            {
                "title": "Practice LeetCode & DSA Graph Algorithms",
                "description": "Solve 3 Dijkstra and Topological Sort problems",
                "priority": "URGENT",
                "status": "COMPLETED",
                "due_date": now - timedelta(days=1),
                "completed_at": now - timedelta(hours=20),
                "estimated_minutes": 90,
                "actual_minutes": 110,
            },
            {
                "title": "Database Indexing & Query Optimization Assignment",
                "description": "Analyze B-Tree vs Hash indexes performance",
                "priority": "MEDIUM",
                "status": "PENDING",
                "due_date": now + timedelta(days=1),
                "estimated_minutes": 45,
                "actual_minutes": 0,
            },
            {
                "title": "Setup Docker Compose Orchestration",
                "description": "Configure multi-stage container build for FastAPI & React",
                "priority": "HIGH",
                "status": "PENDING",
                "due_date": now + timedelta(days=2),
                "estimated_minutes": 30,
                "actual_minutes": 0,
            },
            {
                "title": "Revise Operating Systems Memory Management",
                "description": "Paging, Segmentation, and Virtual Memory concepts",
                "priority": "LOW",
                "status": "PENDING",
                "due_date": now + timedelta(days=3),
                "estimated_minutes": 60,
                "actual_minutes": 0,
            },
        ]

        # Batch-insert all tasks in a single commit (avoids per-row commits).
        tasks = [models.Task(user_id=user.id, **t_data) for t_data in seed_tasks]
        db.add_all(tasks)
        db.commit()
        for t in tasks:
            db.refresh(t)

        rag = get_rag_service()
        for t in tasks:
            action = "COMPLETE" if t.status == "COMPLETED" else "CREATE"
            mem_text = format_task_memory(
                action,
                {
                    "title": t.title,
                    "priority": t.priority,
                    "estimated_minutes": t.estimated_minutes,
                    "actual_minutes": t.actual_minutes,
                    "due_date": t.due_date.strftime("%Y-%m-%d") if t.due_date else None,
                },
            )
            try:
                rag.store_memory_from_task(
                    user_id=user.id,
                    task_id=t.id,
                    action=action,
                    content=mem_text,
                    task_title=t.title,
                    priority=t.priority,
                    status=t.status,
                    due_date=t.due_date,
                    completed_at=t.completed_at,
                    estimated_minutes=t.estimated_minutes,
                    actual_minutes=t.actual_minutes,
                )
            except MemoryIngestionError as exc:
                logger.error("Seed memory failed for task %s: %s", t.id, exc)

        extra_mems = [
            "Postponed Database assignment three times last week due to overlap with exam prep.",
            "Completed System Design study session in 50 minutes, 10 minutes faster than estimate.",
            "Finished DSA practice two days late due to algorithmic debugging.",
            "Consistently complete high-priority coding tasks best between 9 AM and 1 PM.",
        ]
        for em in extra_mems:
            try:
                rag.store_memory_from_task(
                    user_id=user.id,
                    task_id=None,
                    action="HISTORICAL_LOG",
                    content=em,
                )
            except MemoryIngestionError as exc:
                logger.error("Seed memory failed: %s", exc)

        logger.info("Seeded demo user and tasks (development only).")
    except Exception as exc:
        db.rollback()
        logger.error("Startup seeding error: %s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_testing:
        # Test fixtures own their in-memory schema.
        logger.info("Testing mode: schema managed by test fixtures.")
    elif settings.is_production:
        _run_migrations(fail_fast=True)
        logger.info("Production mode: schema management via Alembic.")
    else:
        _run_migrations(fail_fast=False)

    if settings.SEED_DEMO and not settings.is_production and not settings.is_testing:
        _seed_demo_data()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="A simplified, cute & cozy task management, analytics, and RAG task memory AI system.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS — restrict to configured origins; never wildcard with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:16]
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-Id"] = request_id
    logger.info(
        "request request_id=%s method=%s path=%s status=%s latency_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# Routers
app.include_router(health_routes.router)
app.include_router(auth_routes.router)
app.include_router(task_routes.router)
app.include_router(analytics_routes.router)
app.include_router(rag_routes.router)


@app.get("/")
def root():
    return {
        "app": "Cozy AI Productivity System",
        "status": "active",
        "aesthetic": "Cute & Cozy Pastels 🌸",
        "rag_engine": "ChromaDB + SentenceTransformers + Grounded RAG Pipeline",
        "docs": "/docs",
    }
