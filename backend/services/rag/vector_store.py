"""Vector store abstraction with a persistent ChromaDB adapter."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.config import settings
from services.rag.embeddings import EmbeddingService

logger = logging.getLogger("cozy.rag.vector_store")


@dataclass
class VectorRecord:
    id: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None
    distance: float | None = None
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "distance": self.distance,
            "score": self.score,
        }


class VectorStore:
    """Interface for a persistent, user-scoped vector store.

    Application RAG logic depends on this abstraction only; the concrete
    ChromaDB adapter lives in :class:`ChromaVectorStore`.
    """

    def add(self, user_id: int, record: VectorRecord) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def update(self, user_id: int, record: VectorRecord) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def delete(self, user_id: int, memory_id: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def search(
        self,
        user_id: int,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:  # pragma: no cover - interface
        raise NotImplementedError

    def get_by_id(self, user_id: int, memory_id: str) -> VectorRecord | None:  # pragma: no cover
        raise NotImplementedError

    def list_by_user(
        self,
        user_id: int,
        limit: int,
        offset: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:  # pragma: no cover
        raise NotImplementedError

    def count(self, user_id: int, where: dict[str, Any] | None = None) -> int:  # pragma: no cover
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB adapter. Never falls back to volatile in-memory."""

    def __init__(self, embeddings: EmbeddingService, path: str | None = None) -> None:
        self._embeddings = embeddings
        self._path = path or settings.CHROMA_PATH
        self._fallback = None
        try:
            import chromadb  # lazy import

            self._client = chromadb.PersistentClient(path=self._path)
        except Exception as exc:
            logger.warning(
                "ChromaDB initialization failed (%s). Falling back to InMemoryVectorStore.", exc
            )
            self._client = None
            self._fallback = InMemoryVectorStore()

    def _collection(self, user_id: int):
        if self._client is None:
            return None
        return self._client.get_or_create_collection(
            name=f"user_{user_id}_memories",
            metadata={"hnsw:space": "cosine"},
        )

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """ChromaDB only accepts str/int/float/bool metadata values."""
        out: dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (bool | int | float | str)):
                out[key] = value
            else:
                out[key] = str(value)
        return out

    def add(self, user_id: int, record: VectorRecord) -> str:
        if self._fallback is not None:
            return self._fallback.add(user_id, record)
        collection = self._collection(user_id)
        embedding = record.embedding or self._embeddings.embed_documents([record.text])[0]
        collection.add(
            ids=[record.id],
            embeddings=[embedding],
            documents=[record.text],
            metadatas=[self._sanitize_metadata(record.metadata)],
        )
        return record.id

    def update(self, user_id: int, record: VectorRecord) -> None:
        if self._fallback is not None:
            return self._fallback.update(user_id, record)
        collection = self._collection(user_id)
        embedding = record.embedding or self._embeddings.embed_documents([record.text])[0]
        collection.update(
            ids=[record.id],
            embeddings=[embedding],
            documents=[record.text],
            metadatas=[self._sanitize_metadata(record.metadata)],
        )

    def delete(self, user_id: int, memory_id: str) -> None:
        if self._fallback is not None:
            return self._fallback.delete(user_id, memory_id)
        self._collection(user_id).delete(ids=[memory_id])

    def search(
        self,
        user_id: int,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        if self._fallback is not None:
            return self._fallback.search(user_id, query_embedding, top_k, where)
        collection = self._collection(user_id)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where or None,
        )
        records: list[VectorRecord] = []
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        for i in range(len(ids)):
            distance = distances[i] if i < len(distances) else 0.0
            records.append(
                VectorRecord(
                    id=ids[i],
                    text=docs[i],
                    metadata=metas[i] or {},
                    distance=distance,
                    score=float(max(0.0, min(1.0, 1.0 - distance))),
                )
            )
        return records

    def get_by_id(self, user_id: int, memory_id: str) -> VectorRecord | None:
        if self._fallback is not None:
            return self._fallback.get_by_id(user_id, memory_id)
        try:
            collection = self._collection(user_id)
            result = collection.get(ids=[memory_id])
            ids = result.get("ids") or []
            if not ids:
                return None
            docs = result.get("documents") or [""]
            metas = result.get("metadatas") or [{}]
            return VectorRecord(id=ids[0], text=docs[0], metadata=metas[0] or {})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("get_by_id failed: %s", exc)
            return None

    def list_by_user(
        self,
        user_id: int,
        limit: int,
        offset: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        if self._fallback is not None:
            return self._fallback.list_by_user(user_id, limit, offset, where)
        collection = self._collection(user_id)
        result = collection.get(limit=limit, offset=offset, where=where or None)
        ids = result.get("ids") or []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        records: list[VectorRecord] = []
        for i in range(len(ids)):
            records.append(
                VectorRecord(id=ids[i], text=docs[i], metadata=metas[i] or {})
            )
        return records

    def count(self, user_id: int, where: dict[str, Any] | None = None) -> int:
        if self._fallback is not None:
            return self._fallback.count(user_id, where)
        collection = self._collection(user_id)
        result = collection.get(where=where or None)
        return len(result.get("ids") or [])


class InMemoryVectorStore(VectorStore):
    """Deterministic in-memory fake, injected explicitly into tests."""

    def __init__(self) -> None:
        self._records: dict[int, dict[str, VectorRecord]] = {}

    def _by_user(self, user_id: int) -> dict[str, VectorRecord]:
        return self._records.setdefault(user_id, {})

    def _filter(
        self, records: list[VectorRecord], where: dict[str, Any] | None
    ) -> list[VectorRecord]:
        if not where:
            return records
        return [
            r
            for r in records
            if all(r.metadata.get(k) == v for k, v in where.items())
        ]

    def add(self, user_id: int, record: VectorRecord) -> str:
        self._by_user(user_id)[record.id] = record
        return record.id

    def update(self, user_id: int, record: VectorRecord) -> None:
        self._by_user(user_id)[record.id] = record

    def delete(self, user_id: int, memory_id: str) -> None:
        self._by_user(user_id).pop(memory_id, None)

    def search(
        self,
        user_id: int,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        candidate = self._filter(list(self._by_user(user_id).values()), where)

        def _similarity(a: list[float], b: list[float]) -> float:
            if not a or not b or len(a) != len(b):
                return 0.0
            dot = sum(x * y for x, y in zip(a, b, strict=False))
            na = sum(x * x for x in a) ** 0.5 or 1.0
            nb = sum(x * x for x in b) ** 0.5 or 1.0
            return dot / (na * nb)

        ranked = sorted(
            candidate,
            key=lambda r: _similarity(query_embedding, r.embedding or []),
            reverse=True,
        )
        for r in ranked:
            r.score = round(_similarity(query_embedding, r.embedding or []), 4)
            r.distance = round(1.0 - r.score, 4)
        return ranked[:top_k]

    def get_by_id(self, user_id: int, memory_id: str) -> VectorRecord | None:
        return self._by_user(user_id).get(memory_id)

    def list_by_user(
        self,
        user_id: int,
        limit: int,
        offset: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorRecord]:
        records = self._filter(
            sorted(
                self._by_user(user_id).values(),
                key=lambda r: r.metadata.get("created_at", ""),
                reverse=True,
            ),
            where,
        )
        return records[offset : offset + limit]

    def count(self, user_id: int, where: dict[str, Any] | None = None) -> int:
        return len(self._filter(list(self._by_user(user_id).values()), where))
