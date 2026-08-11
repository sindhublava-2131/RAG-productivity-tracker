"""Embedding service abstraction."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from core.config import settings

logger = logging.getLogger("cozy.rag.embeddings")


class EmbeddingService:
    """Produces document/query embeddings.

    The real implementation lazily loads a SentenceTransformer model (once) and
    reuses it across calls. If loading fails (e.g. disk or dependency limits),
    it falls back gracefully to deterministic lightweight embeddings.
    """

    model_name: str

    def __init__(self, model_name: str | None = None, dimension: int | None = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # lazy import

                logger.info("Loading embedding model %s (first use)...", self.model_name)
                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model %s loaded.", self.model_name)
            except Exception as exc:
                logger.warning(
                    "Could not load SentenceTransformer (%s). Using lightweight embeddings.", exc
                )
                self._model = "fallback"
        return self._model

    def _fallback_vector(self, text: str) -> list[float]:
        base = [float((ord(c) % 13) + 1) for c in text[: self.dimension]]
        while len(base) < self.dimension:
            base.append(0.0)
        norm = sum(x * x for x in base) ** 0.5 or 1.0
        return [round(x / norm, 6) for x in base]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load_model()
        if model == "fallback":
            return [self._fallback_vector(t) for t in texts]
        vectors = model.encode(list(texts)).tolist()
        return [self._normalize(v) for v in vectors]

    def embed_query(self, query: str) -> list[float]:
        model = self._load_model()
        if model == "fallback":
            return self._fallback_vector(query)
        vector = model.encode([query])[0].tolist()
        return self._normalize(vector)

    def _normalize(self, vector: list[float]) -> list[float]:
        return [round(float(x), 6) for x in vector]

    @property
    def dimension_used(self) -> int:
        return self.dimension


class FakeEmbeddingService(EmbeddingService):
    """Deterministic embedding service for tests (no network/model download)."""

    def __init__(self, model_name: str = "fake-mini", dimension: int = 8) -> None:
        super().__init__(model_name=model_name, dimension=dimension)

    def _vector_for(self, text: str) -> list[float]:
        base = [float((ord(c) % 7) + 1) for c in text[: self.dimension]]
        while len(base) < self.dimension:
            base.append(0.0)
        norm = sum(x * x for x in base) ** 0.5 or 1.0
        return [round(x / norm, 6) for x in base]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector_for(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._vector_for(query)
