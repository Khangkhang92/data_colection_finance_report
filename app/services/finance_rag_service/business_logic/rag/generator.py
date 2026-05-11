from __future__ import annotations

from openai import OpenAI

from common.config.finance_rag import Settings
from business_logic.rag.prompts import CHAT_SYSTEM_PROMPT


class RagGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        api_key = settings.novita_api_key or settings.openai_api_key
        base_url = settings.novita_base_url or settings.openai_base_url or None
        self.model = settings.novita_model or settings.openai_model
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    def generate_answer(self, question: str, contexts: list[str]) -> str:
        if not contexts:
            return "No relevant context found in local finance documents."

        if self.client is None:
            return self._fallback_answer(question, contexts)

        context_text = "\n\n".join(f"[{idx + 1}] {c}" for idx, c in enumerate(contexts))
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\n"
                        "Context:\n"
                        f"{context_text}"
                    ),
                },
            ],
            temperature=0.1,
        )
        return response.output_text.strip()

    @staticmethod
    def _fallback_answer(question: str, contexts: list[str]) -> str:
        del question
        return (
            "No LLM API key is configured (NOVITA_API_KEY or OPENAI_API_KEY), running retrieval-only mode. "
            f"Top context: {contexts[0][:300]}"
        )
