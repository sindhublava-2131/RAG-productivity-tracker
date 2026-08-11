"""Bounded context construction for grounded generation."""

from __future__ import annotations

from core.config import settings
from services.rag.vector_store import VectorRecord


class SourceBlock:
    __slots__ = ("id", "task_id", "task_title", "action", "content", "created_at", "score")

    def __init__(self, record: VectorRecord) -> None:
        md = record.metadata
        self.id = record.id
        self.task_id = md.get("task_id") or None
        self.task_title = md.get("task_title")
        self.action = md.get("action")
        self.content = record.text
        self.created_at = md.get("created_at")
        self.score = record.score

    def to_citation(self) -> dict:
        task_id: int | None = None
        raw_task_id = self.task_id
        if raw_task_id is not None:
            try:
                task_id = int(raw_task_id)
            except (TypeError, ValueError):
                task_id = None
        return {
            "id": self.id,
            "task_id": task_id,
            "content": self.content,
            "score": float(self.score or 0.0),
            "created_at": self.created_at,
        }

    def format(self) -> str:
        task_line = f"Task: {self.task_title}" if self.task_title else "Task: N/A"
        action_line = f"Action: {self.action}" if self.action else "Action: N/A"
        date_line = f"Date: {self.created_at}" if self.created_at else "Date: N/A"
        return (
            f"[Source: {self.id}]\n"
            f"{task_line}\n"
            f"{action_line}\n"
            f"{date_line}\n"
            f"Content: {self.content}"
        )


class ContextBuilder:
    """Builds a bounded, deduplicated context from ranked sources."""

    def __init__(
        self,
        max_sources: int | None = None,
        max_context_chars: int | None = None,
    ) -> None:
        self.max_sources = max_sources or settings.RAG_MAX_SOURCES
        self.max_context_chars = max_context_chars or settings.RAG_MAX_CONTEXT_CHARS

    def build(self, records: list[VectorRecord]) -> list[SourceBlock]:
        seen_ids = set()
        blocks: list[SourceBlock] = []
        total_chars = 0

        for record in records:
            if record.id in seen_ids:
                continue
            seen_ids.add(record.id)

            block = SourceBlock(record)
            formatted = block.format()
            if total_chars + len(formatted) > self.max_context_chars:
                break
            total_chars += len(formatted) + 1
            blocks.append(block)
            if len(blocks) >= self.max_sources:
                break

        return blocks

    def render_prompt_context(self, blocks: list[SourceBlock]) -> str:
        if not blocks:
            return "No relevant task history found for this query."
        return "\n\n".join(b.format() for b in blocks)


def build_context(records: list[VectorRecord]) -> list[SourceBlock]:
    """Convenience wrapper used by the pipeline."""
    return ContextBuilder().build(records)
