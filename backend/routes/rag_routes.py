from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

import auth
import models
import schemas
from core.config import settings
from core.rate_limit import rate_limit
from services.rag.service import get_rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG AI Memory & Assistant"])


def _parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp from vector metadata into a tz-aware datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _validate_model_allowlist(provider: str | None, model_name: str | None) -> None:
    """Reject model names outside the per-provider allowlist (LLM cost abuse guard)."""
    name = (provider or settings.RAG_PROVIDER or "ollama").lower()
    allowed = settings.ALLOWED_MODELS.get(name, [])
    if allowed and model_name and model_name not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_name}' is not allowed for provider '{name}'. "
            f"Allowed: {', '.join(allowed)}",
        )


@router.post("/query", response_model=schemas.RAGQueryResponse)
async def query_rag_assistant(
    req: schemas.RAGQueryRequest,
    current_user: models.User = Depends(auth.get_current_user),
    _: None = Depends(rate_limit("rag-query", limit=30)),
):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    _validate_model_allowlist(req.provider, req.model_name)

    rag = get_rag_service()
    result = await rag.query(
        user_id=current_user.id,
        user_name=current_user.name,
        question=req.question,
        provider=req.provider,
        model_name=req.model_name,
    )
    return schemas.RAGQueryResponse(**result)


@router.get("/memories", response_model=schemas.MemoryListResponse)
def get_user_rag_memories(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    task_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    current_user: models.User = Depends(auth.get_current_user),
):
    rag = get_rag_service()
    records, total = rag.list_memories(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        task_id=task_id,
        action=action,
    )

    items: list[schemas.MemoryRecord] = []
    for r in records:
        md = r.metadata
        items.append(
            schemas.MemoryRecord(
                id=r.id,
                user_id=current_user.id,
                task_id=int(md["task_id"]) if str(md.get("task_id", "")).isdigit() else None,
                action=md.get("action"),
                content=r.text,
                created_at=_parse_iso(md.get("created_at") or "") or datetime.now(UTC),
                source_type=md.get("source_type"),
                source_id=md.get("source_id"),
                embedding_model=md.get("embedding_model"),
                schema_version=int(md.get("schema_version", 1)),
                task_title=md.get("task_title"),
                priority=md.get("priority"),
                status=md.get("status"),
                due_date=_parse_iso(md.get("due_date") or ""),
                completed_at=_parse_iso(md.get("completed_at") or ""),
                estimated_minutes=md.get("estimated_minutes"),
                actual_minutes=md.get("actual_minutes"),
            )
        )

    has_more = offset + len(items) < total
    return schemas.MemoryListResponse(
        items=items, total=total, limit=limit, offset=offset, has_more=has_more
    )


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: str,
    current_user: models.User = Depends(auth.get_current_user),
):
    rag = get_rag_service()
    record = rag.vector_store.get_by_id(current_user.id, memory_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    rag.vector_store.delete(current_user.id, memory_id)
