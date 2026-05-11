from __future__ import annotations

from dataclasses import dataclass

from common.config.finance_rag import Settings


def estimate_tokens(text: str) -> int:
    # Fast approximate estimator for runtime safety.
    return max(1, len(text) // 4)


def truncate_text(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


@dataclass
class BudgetedContexts:
    vector_contexts: list[str]
    graph_contexts: list[str]


class TokenBudgetManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def allocate(self, vector_contexts: list[str], graph_contexts: list[str]) -> BudgetedContexts:
        vector_budget = min(self.settings.max_vector_context_tokens, self.settings.max_context_tokens)
        graph_budget = min(self.settings.max_graph_context_tokens, max(0, self.settings.max_context_tokens - vector_budget))

        v = self._fit_contexts(vector_contexts, vector_budget)
        g = self._fit_contexts(graph_contexts, graph_budget)
        return BudgetedContexts(vector_contexts=v, graph_contexts=g)

    def _fit_contexts(self, contexts: list[str], budget_tokens: int) -> list[str]:
        if budget_tokens <= 0:
            return []
        out: list[str] = []
        used = 0
        for c in contexts:
            cost = estimate_tokens(c)
            if used + cost <= budget_tokens:
                out.append(c)
                used += cost
                continue
            remaining = budget_tokens - used
            if remaining > 32:
                out.append(truncate_text(c, remaining))
            break
        return out

