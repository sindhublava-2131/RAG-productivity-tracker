"""RAG service container — lazy wiring of embeddings, vector store, pipeline, memory."""

from __future__ import annotations

import logging
from typing import Any

from services.rag.embeddings import EmbeddingService
from services.rag.memory import MemoryIngestionService
from services.rag.pipeline import RagPipeline
from services.rag.vector_store import ChromaVectorStore, VectorRecord, VectorStore

logger = logging.getLogger("cozy.rag.service")


class RagService:
    """Composition root for the RAG subsystem.

    Components are created lazily on first use so importing this module never
    downloads an embedding model or opens ChromaDB. Tests inject fakes via the
    constructor.
    """

    def __init__(
        self,
        *,
        vector_store: VectorStore | None = None,
        embeddings: EmbeddingService | None = None,
        memory_service: MemoryIngestionService | None = None,
        pipeline: RagPipeline | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings
        self._memory_service = memory_service
        self._pipeline = pipeline

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = ChromaVectorStore(embeddings=self.embeddings)
        return self._vector_store

    @property
    def embeddings(self) -> EmbeddingService:
        if self._embeddings is None:
            self._embeddings = EmbeddingService()
        return self._embeddings

    @property
    def memory_service(self) -> MemoryIngestionService:
        if self._memory_service is None:
            self._memory_service = MemoryIngestionService(
                vector_store=self.vector_store, embeddings=self.embeddings
            )
        return self._memory_service

    @property
    def pipeline(self) -> RagPipeline:
        if self._pipeline is None:
            self._pipeline = RagPipeline(
                vector_store=self.vector_store, embeddings=self.embeddings
            )
        return self._pipeline

    def store_memory_from_task(
        self,
        *,
        user_id: int,
        task_id: int | None,
        action: str,
        content: str,
        task_title: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        due_date: Any = None,
        completed_at: Any = None,
        estimated_minutes: int | None = None,
        actual_minutes: int | None = None,
    ) -> str:
        memory = self.memory_service.build_memory(
            user_id=user_id,
            task_id=task_id,
            action=action,
            content=content,
            task_title=task_title,
            priority=priority,
            status=status,
            due_date=due_date,
            completed_at=completed_at,
            estimated_minutes=estimated_minutes,
            actual_minutes=actual_minutes,
        )
        return self.memory_service.store(memory)

    async def query(
        self,
        *,
        user_id: int,
        user_name: str,
        question: str,
        provider: str | None = None,
        model_name: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.pipeline.run(
            user_id=user_id,
            user_name=user_name,
            question=question,
            provider=provider,
            model_name=model_name,
            filters=filters,
        )

    def list_memories(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        task_id: int | None = None,
        action: str | None = None,
    ) -> tuple[list[VectorRecord], int]:
        where: dict[str, Any] = {}
        if task_id is not None:
            where["task_id"] = str(task_id)
        if action:
            where["action"] = action.upper()
        records = self.vector_store.list_by_user(
            user_id=user_id, limit=limit, offset=offset, where=where or None
        )
        total = self.vector_store.count(user_id=user_id, where=where or None)
        return records, total


_rag_service: RagService | None = None


def get_rag_service() -> RagService:
    """Return the process-wide RAG service singleton (lazy)."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service


def configure_rag_service(service: RagService) -> None:
    """Install a pre-built RagService as the process-wide singleton.

    Used by tests to inject fakes (InMemoryVectorStore, FakeEmbeddingService,
    FakeLLMProvider) so the app runs fully offline.
    """
    global _rag_service
    _rag_service = service


def reset_rag_service() -> None:
    """Reset the singleton — used by tests to inject fakes."""
    global _rag_service
    _rag_service = None
