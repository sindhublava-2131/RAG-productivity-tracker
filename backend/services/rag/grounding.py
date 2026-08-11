"""Citation extraction and grounding validation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from services.rag.context import SourceBlock

_CITATION_RE = re.compile(r"\[(?:Source|src|cite)[:\s-]*([A-Za-z0-9_-]+)\]", re.IGNORECASE)


@dataclass
class GroundingResult:
    valid_source_ids: list[str]
    invalid_source_ids: list[str]
    grounded: bool


class GroundingValidator:
    """Validates that cited source IDs exist in the actual retrieved set.

    Never allows the LLM to invent source IDs: references to non-retrieved
    sources are rejected, and an answer with no valid evidence is ungrounded.
    """

    def validate(self, answer: str, sources: list[SourceBlock]) -> GroundingResult:
        allowed = {block.id for block in sources}
        cited = set(_CITATION_RE.findall(answer))
        valid = sorted(cited & allowed)
        invalid = sorted(cited - allowed)
        grounded = bool(valid) and not invalid and len(cited) > 0
        return GroundingResult(
            valid_source_ids=valid,
            invalid_source_ids=invalid,
            grounded=grounded,
        )
