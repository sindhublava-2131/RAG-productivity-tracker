from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import text

import schemas
from database import engine

router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=schemas.HealthResponse)
def liveness():
    return schemas.HealthResponse(
        status="ok",
        app="Cozy AI Productivity System",
        version="2.1.0",
        timestamp=datetime.now(UTC),
    )


@router.get("/health/ready", response_model=schemas.ReadinessResponse)
def readiness(response: Response):
    checks: dict = {"database": "ok"}
    ready = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - defensive
        checks["database"] = f"error: {exc}"
        ready = False

    # Report the vector store backend so silent in-memory degradation is visible.
    try:
        from services.rag.service import get_rag_service

        rag = get_rag_service()
        checks["rag_vector_store"] = rag.vector_store.mode
        if rag.vector_store.mode == "in-memory-fallback":
            ready = False
    except Exception as exc:  # pragma: no cover - defensive
        checks["rag_vector_store"] = f"error: {exc}"
        ready = False

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return schemas.ReadinessResponse(status="not_ready", checks=checks)
    return schemas.ReadinessResponse(status="ready", checks=checks)
