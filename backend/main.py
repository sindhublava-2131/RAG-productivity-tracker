from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import models
from database import engine, Base, SessionLocal
from routes import auth_routes, task_routes, analytics_routes, rag_routes
import auth
import rag_service

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cozy AI Productivity & RAG Intelligence System",
    description="A simplified, cute & cozy task management, analytics, and RAG task memory AI system.",
    version="2.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_routes.router)
app.include_router(task_routes.router)
app.include_router(analytics_routes.router)
app.include_router(rag_routes.router)

@app.on_event("startup")
def seed_default_user_and_memories():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == "demo@cozy.app").first()
        if not user:
            # Create Demo User
            user = models.User(
                name="Cozy User 🌸",
                email="demo@cozy.app",
                password_hash=auth.get_password_hash("cozy123")
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            now = datetime.utcnow()
            # Seed Tasks
            seed_tasks = [
                {
                    "title": "Complete React Component Architecture Assignment",
                    "description": "Build modular TypeScript components with Tailwind styling",
                    "priority": "HIGH",
                    "status": "COMPLETED",
                    "due_date": now - timedelta(hours=5),
                    "completed_at": now - timedelta(hours=2),
                    "estimated_minutes": 60,
                    "actual_minutes": 45
                },
                {
                    "title": "Practice LeetCode & DSA Graph Algorithms",
                    "description": "Solve 3 Dijkstra and Topological Sort problems",
                    "priority": "URGENT",
                    "status": "COMPLETED",
                    "due_date": now - timedelta(days=1),
                    "completed_at": now - timedelta(hours=20),
                    "estimated_minutes": 90,
                    "actual_minutes": 110
                },
                {
                    "title": "Database Indexing & Query Optimization Assignment",
                    "description": "Analyze B-Tree vs Hash indexes performance",
                    "priority": "MEDIUM",
                    "status": "PENDING",
                    "due_date": now + timedelta(days=1),
                    "estimated_minutes": 45,
                    "actual_minutes": 0
                },
                {
                    "title": "Setup Docker Compose Orchestration",
                    "description": "Configure multi-stage container build for FastAPI & React",
                    "priority": "HIGH",
                    "status": "PENDING",
                    "due_date": now + timedelta(days=2),
                    "estimated_minutes": 30,
                    "actual_minutes": 0
                },
                {
                    "title": "Revise Operating Systems Memory Management",
                    "description": "Paging, Segmentation, and Virtual Memory concepts",
                    "priority": "LOW",
                    "status": "PENDING",
                    "due_date": now + timedelta(days=3),
                    "estimated_minutes": 60,
                    "actual_minutes": 0
                }
            ]

            for t_data in seed_tasks:
                t = models.Task(user_id=user.id, **t_data)
                db.add(t)
                db.commit()
                db.refresh(t)

                # Generate RAG memory
                action = "COMPLETE" if t.status == "COMPLETED" else "CREATE"
                mem_text = rag_service.format_task_memory(action, {
                    "title": t.title,
                    "priority": t.priority,
                    "estimated_minutes": t.estimated_minutes,
                    "actual_minutes": t.actual_minutes,
                    "due_date": t.due_date.strftime("%Y-%m-%d") if t.due_date else None
                })
                rag_service.store_memory(user.id, mem_text, action, t.id)

            # Extra historical memory entries for deep RAG insights
            extra_mems = [
                "Postponed Database assignment three times last week due to overlap with exam prep.",
                "Completed System Design study session in 50 minutes, 10 minutes faster than estimate.",
                "Finished DSA practice two days late due to algorithmic debugging.",
                "Consistently complete high-priority coding tasks best between 9 AM and 1 PM."
            ]
            for em in extra_mems:
                rag_service.store_memory(user.id, em, "HISTORICAL_LOG")

    except Exception as e:
        db.rollback()
        print(f"Startup seeding error: {e}")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "app": "Cozy AI Productivity System",
        "status": "active",
        "aesthetic": "Cute & Cozy Pastels 🌸",
        "rag_engine": "ChromaDB + SentenceTransformers + Multi-Agent LLM",
        "docs": "/docs"
    }
