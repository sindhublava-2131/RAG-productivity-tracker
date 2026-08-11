"""Structured RAG memory model and the canonical memory-ingestion service."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from services.rag.embeddings import EmbeddingService
from services.rag.vector_store import VectorRecord, VectorStore

logger = logging.getLogger("cozy.rag.memory")

MEMORY_SCHEMA_VERSION = 1


@dataclass
class MemoryRecord:
    id: str
    user_id: int
    task_id: int | None
    action: str
    content: str
    created_at: datetime
    source_type: str
    source_id: str | None
    embedding_model: str
    schema_version: int = MEMORY_SCHEMA_VERSION
    task_title: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None
    embedding: list | None = None

    def metadata_dict(self) -> dict[str, Any]:
        md: dict[str, Any] = {
            "user_id": str(self.user_id),
            "task_id": str(self.task_id) if self.task_id is not None else "",
            "action": self.action,
            "created_at": self.created_at.isoformat(),
            "source_type": self.source_type,
            "source_id": self.source_id or "",
            "embedding_model": self.embedding_model,
            "schema_version": self.schema_version,
        }
        optional_fields: dict[str, Any] = {
            "task_title": self.task_title,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "estimated_minutes": self.estimated_minutes,
            "actual_minutes": self.actual_minutes,
        }
        for key, value in optional_fields.items():
            if value is not None and value != "":
                md[key] = value
        return md

    def to_vector_record(self) -> VectorRecord:
        return VectorRecord(
            id=self.id,
            text=self.content,
            metadata=self.metadata_dict(),
            embedding=self.embedding,
        )


class MemoryIngestionError(RuntimeError):
    """Raised when a memory could not be persisted to the vector store."""


class MemoryIngestionService:
    """Canonical path for turning task lifecycle events into structured memories.

    Only creates the vector memory after the caller commits the database
    operation. If vector persistence fails, an exception propagates so the
    failure is visible rather than silently swallowed.
    """

    def __init__(self, vector_store: VectorStore, embeddings: EmbeddingService) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings

    def build_memory(
        self,
        *,
        user_id: int,
        task_id: int | None,
        action: str,
        content: str,
        created_at: datetime | None = None,
        task_title: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        due_date: datetime | None = None,
        completed_at: datetime | None = None,
        estimated_minutes: int | None = None,
        actual_minutes: int | None = None,
        source_type: str = "task_event",
        source_id: str | None = None,
    ) -> MemoryRecord:
        return MemoryRecord(
            id=f"mem_{uuid.uuid4().hex}",
            user_id=user_id,
            task_id=task_id,
            action=action,
            content=content,
            created_at=created_at or datetime.now(UTC),
            source_type=source_type,
            source_id=source_id,
            embedding_model=self._embeddings.model_name,
            task_title=task_title,
            priority=priority,
            status=status,
            due_date=due_date,
            completed_at=completed_at,
            estimated_minutes=estimated_minutes,
            actual_minutes=actual_minutes,
        )

    def store(self, memory: MemoryRecord) -> str:
        """Persist a memory to the vector store, computing embeddings.

        Raises MemoryIngestionError on failure so callers never believe a
        memory was indexed when it was not.
        """
        try:
            memory.embedding = self._embeddings.embed_documents([memory.content])[0]
            return self._vector_store.add(memory.user_id, memory.to_vector_record())
        except Exception as exc:
            logger.error(
                "Memory persistence failed for user_id=%s task_id=%s: %s",
                memory.user_id,
                memory.task_id,
                exc,
            )
            raise MemoryIngestionError(
                f"Failed to persist memory: {exc}"
            ) from exc

    def delete(self, user_id: int, memory_id: str) -> None:
        self._vector_store.delete(user_id, memory_id)


def format_task_memory(action: str, task_data: dict[str, Any]) -> str:
    """Convert structured task lifecycle events into natural-language memories."""
    title = task_data.get("title", "Task")
    priority = (task_data.get("priority") or "MEDIUM").lower()
    est = task_data.get("estimated_minutes") or 0
    actual = task_data.get("actual_minutes") or 0
    due_date = task_data.get("due_date")
    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")

    if action == "CREATE":
        est_str = f" with an estimate of {est} minutes" if est > 0 else ""
        due_str = f" due on {due_date}" if due_date else ""
        return f"Created {priority}-priority task '{title}'{est_str}{due_str} on {now_str}."

    if action == "COMPLETE":
        time_str = f" in {actual} minutes" if actual > 0 else ""
        diff_str = ""
        if est > 0 and actual > 0:
            diff = est - actual
            if diff > 0:
                diff_str = f", finished {diff} minutes faster than estimated"
            elif diff < 0:
                diff_str = f", took {abs(diff)} minutes longer than estimated"
        return f"Completed '{title}'{time_str}{diff_str} on {now_str}."

    if action == "DELAY":
        delay_reason = task_data.get("delay_note", "due date pushed")
        return f"Postponed '{title}' ({priority} priority) on {now_str}. Note: {delay_reason}."

    if action == "OVERDUE":
        return f"Task '{title}' ({priority} priority) became overdue past its due date ({due_date})."

    if action == "UPDATE":
        status = task_data.get("status", "updated")
        return f"Updated task '{title}': status changed to {status}, spent {actual} minutes on {now_str}."

    return f"Action '{action}' recorded on task '{title}' at {now_str}."
