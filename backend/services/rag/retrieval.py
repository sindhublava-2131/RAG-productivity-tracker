"""Hybrid retrieval: semantic + metadata filter + lexical relevance."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from services.rag.embeddings import EmbeddingService
from services.rag.vector_store import VectorRecord, VectorStore

logger = logging.getLogger("cozy.rag.retrieval")

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set:
    return set(_WORD_RE.findall(text.lower()))


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _lexical_relevance(query: str, text: str) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    d_tokens = _tokenize(text)
    if not d_tokens:
        return 0.0
    overlap = len(q_tokens & d_tokens)
    return overlap / len(q_tokens)


class HybridRetriever:
    """Retrieves user-scoped candidate memories.

    User isolation is enforced *during* retrieval: every store call is scoped by
    ``user_id`` and a mandatory ``where`` metadata filter on ``user_id``.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embeddings: EmbeddingService,
        top_k: int,
        lexical_weight: float = 0.3,
    ) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings
        self.top_k = top_k
        self.lexical_weight = lexical_weight

    def retrieve(
        self,
        user_id: int,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        normalized = _normalize_query(query)
        if not normalized:
            return []

        where: dict[str, Any] = {"user_id": str(user_id)}
        if filters:
            for key, value in filters.items():
                if value is not None:
                    where[key] = value if isinstance(value, str) else str(value)

        query_embedding = self._embeddings.embed_query(normalized)
        semantic = self._vector_store.search(
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=top_k or self.top_k,
            where=where,
        )

        # Combine semantic similarity with lexical relevance.
        for record in semantic:
            sem_score = record.score if record.score is not None else 0.0
            lex_score = _lexical_relevance(normalized, record.text)
            combined = (1.0 - self.lexical_weight) * sem_score + self.lexical_weight * lex_score
            record.score = round(combined, 4)
            record.metadata["semantic_score"] = round(sem_score, 4)
            record.metadata["lexical_score"] = round(lex_score, 4)

        semantic.sort(key=lambda r: (r.score or 0.0), reverse=True)
        return semantic

    @staticmethod
    def extract_filters(
        task_id: int | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if task_id is not None:
            filters["task_id"] = str(task_id)
        if action:
            filters["action"] = action.upper()
        # Date-range filtering is applied post-retrieval by the caller for
        # ChromaDB records whose created_at lives in metadata.
        return filters
