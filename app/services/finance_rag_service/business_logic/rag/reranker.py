from __future__ import annotations


class SimpleScoreReranker:
    def rerank(self, question: str, candidates: list[dict]) -> list[dict]:
        del question
        # v1: score-only rerank. Prepared for model-based reranker in later versions.
        return sorted(candidates, key=lambda x: float(x.get("score", 0.0)), reverse=True)

