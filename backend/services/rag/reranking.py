"""Deterministic reranking of retrieved candidates."""

from __future__ import annotations

from datetime import UTC, datetime

from services.rag.vector_store import VectorRecord


def _recency_bonus(created_at_iso: str | None, now: datetime) -> float:
    if not created_at_iso:
        return 0.0
    try:
        created = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        age_days = max(0.0, (now - created).total_seconds() / 86400.0)
        return max(0.0, 1.0 - age_days / 30.0)  # linear decay over 30 days
    except ValueError:
        return 0.0


class Reranker:
    """Combines scoring components into a deterministic final score.

    Factors:
      - semantic similarity (0..1) from the vector store / hybrid retrieval
      - lexical relevance (0..1)
      - metadata relevance (exact task_id / action match)
      - recency (0..1)
    """

    def __init__(
        self,
        semantic_weight: float = 0.5,
        lexical_weight: float = 0.25,
        metadata_weight: float = 0.15,
        recency_weight: float = 0.1,
    ) -> None:
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        self.metadata_weight = metadata_weight
        self.recency_weight = recency_weight

    def score_record(self, record: VectorRecord, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)

        semantic = float(record.metadata.get("semantic_score", record.score or 0.0))
        lexical = float(record.metadata.get("lexical_score", 0.0))
        metadata = 0.0
        for key in ("task_id", "action"):
            value = record.metadata.get(key)
            if value not in (None, ""):
                metadata = max(metadata, 1.0)
        recency = _recency_bonus(record.metadata.get("created_at"), now)

        total = (
            self.semantic_weight * semantic
            + self.lexical_weight * lexical
            + self.metadata_weight * metadata
            + self.recency_weight * recency
        )
        return round(min(1.0, max(0.0, total)), 4)

    def rerank(
        self,
        records: list[VectorRecord],
        threshold: float,
        limit: int | None = None,
        now: datetime | None = None,
    ) -> list[VectorRecord]:
        scored: list[VectorRecord] = []
        for record in records:
            record.score = self.score_record(record, now=now)
            record.metadata["final_score"] = record.score
            scored.append(record)

        scored.sort(key=lambda r: r.score or 0.0, reverse=True)

        passed = [r for r in scored if (r.score or 0.0) >= threshold]
        if limit is not None:
            return passed[:limit]
        return passed
