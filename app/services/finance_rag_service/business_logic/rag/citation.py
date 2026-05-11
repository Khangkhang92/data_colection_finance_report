from __future__ import annotations

from pydantic import BaseModel


class CitationValidationResult(BaseModel):
    ok: bool
    message: str = ""


class CitationGroundingValidator:
    def validate(self, answer: str, sources: list[dict]) -> CitationValidationResult:
        if not answer.strip():
            return CitationValidationResult(ok=False, message="empty answer")
        if not sources:
            return CitationValidationResult(ok=False, message="missing source refs")
        # Require at least one source-like marker in answer for grounding.
        markers = ["[1]", "Sources:", "source:", "refs:"]
        if not any(m.lower() in answer.lower() for m in markers):
            return CitationValidationResult(ok=False, message="answer missing citation marker")
        return CitationValidationResult(ok=True, message="ok")

