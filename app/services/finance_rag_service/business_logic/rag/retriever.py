from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass
class Chunk:
    chunk_id: int
    content: str


class LocalRetriever:
    def __init__(self, doc_path: str) -> None:
        self.doc_path = Path(doc_path)
        self.chunks = self._load_chunks()

    def _load_chunks(self) -> list[Chunk]:
        if not self.doc_path.exists():
            return []

        raw = self.doc_path.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
        return [Chunk(chunk_id=i + 1, content=block) for i, block in enumerate(blocks)]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(t.lower() for t in TOKEN_RE.findall(text))

    def query(self, question: str, top_k: int) -> list[tuple[Chunk, float]]:
        q_tokens = self._tokens(question)
        if not q_tokens or not self.chunks:
            return []

        scored: list[tuple[Chunk, float]] = []
        for chunk in self.chunks:
            c_tokens = self._tokens(chunk.content)
            overlap = q_tokens & c_tokens
            score = len(overlap) / (len(q_tokens) or 1)
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
