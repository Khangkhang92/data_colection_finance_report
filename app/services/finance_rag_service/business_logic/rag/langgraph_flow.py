from __future__ import annotations

from typing import TypedDict

from business_logic.rag.generator import RagGenerator
from business_logic.rag.graph_store import GraphContextProvider
from business_logic.rag.reranker import SimpleScoreReranker
from business_logic.rag.token_budget import TokenBudgetManager
from business_logic.rag.vector_store import VectorRetriever
from common.config.finance_rag import Settings


class RagState(TypedDict):
    question: str
    top_k: int
    vector_contexts: list[str]
    graph_contexts: list[str]
    source_refs: list[dict]
    answer: str


class FinanceRagFlow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.vector_retriever = VectorRetriever(settings)
        self.graph_provider = GraphContextProvider(settings)
        self.generator = RagGenerator(settings)
        self.reranker = SimpleScoreReranker()
        self.budget = TokenBudgetManager(settings)

    def run(self, question: str, top_k: int) -> RagState:
        # Optional dependency runtime guard.
        try:
            from langgraph.graph import END, START, StateGraph
        except Exception:
            vector_contexts = self._vector_context_node({"question": question, "top_k": top_k})["vector_contexts"]
            graph_contexts = self._graph_context_node({"question": question})["graph_contexts"]
            answer = self._answer_node(
                {"question": question, "vector_contexts": vector_contexts, "graph_contexts": graph_contexts}
            )["answer"]
            return {
                "question": question,
                "top_k": top_k,
                "vector_contexts": vector_contexts,
                "graph_contexts": graph_contexts,
                "source_refs": self._source_refs_from_contexts(vector_contexts),
                "answer": answer,
            }

        graph = StateGraph(RagState)
        graph.add_node("vector_context", self._vector_context_node)
        graph.add_node("graph_context", self._graph_context_node)
        graph.add_node("answer", self._answer_node)

        graph.add_edge(START, "vector_context")
        graph.add_edge("vector_context", "graph_context")
        graph.add_edge("graph_context", "answer")
        graph.add_edge("answer", END)

        compiled = graph.compile()
        state = compiled.invoke({"question": question, "top_k": top_k})
        return state

    def _vector_context_node(self, state: dict) -> dict[str, list[str]]:
        docs_with_scores = self.vector_retriever.retrieve_with_scores(state["question"], top_k=state.get("top_k", 3))
        candidates = [
            {
                "content": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata or {},
            }
            for doc, score in docs_with_scores
        ]
        reranked = self.reranker.rerank(state["question"], candidates)
        return {
            "vector_contexts": [x["content"] for x in reranked],
            "source_refs": [
                {
                    "type": "vector",
                    "chunk_id": x["metadata"].get("chunk_id"),
                    "score": x["score"],
                }
                for x in reranked
            ],
        }

    def _graph_context_node(self, state: dict) -> dict[str, list[str]]:
        snippets = self.graph_provider.fetch_context(state["question"], limit=5)
        return {"graph_contexts": snippets}

    def _answer_node(self, state: dict) -> dict[str, str]:
        vector_contexts = list(state.get("vector_contexts", []))
        graph_contexts = list(state.get("graph_contexts", []))
        budgeted = self.budget.allocate(vector_contexts, graph_contexts)
        contexts = list(budgeted.vector_contexts)
        graph_contexts = budgeted.graph_contexts
        if graph_contexts:
            contexts.append("Graph facts:\n" + "\n".join(graph_contexts))
        answer = self.generator.generate_answer(state["question"], contexts)
        return {"answer": answer}

    @staticmethod
    def _source_refs_from_contexts(contexts: list[str]) -> list[dict]:
        return [{"type": "vector", "chunk_id": i + 1} for i, _ in enumerate(contexts)]
