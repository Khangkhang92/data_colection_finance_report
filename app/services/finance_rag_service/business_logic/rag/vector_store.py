from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from langchain_core.documents import Document
from sqlalchemy import text
from sqlalchemy.orm import Session

from business_logic.rag.retriever import LocalRetriever
from common.config.finance_rag import Settings


def compute_content_hash(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def compute_chunk_hash(content: str, metadata: dict[str, Any]) -> str:
    payload = {"content": content, "metadata": metadata}
    raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class ChunkPayload:
    chunk_id: str
    content: str
    metadata: dict[str, Any]


class VectorRetriever:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def retrieve(self, question: str, top_k: int) -> list[Document]:
        return [doc for doc, _ in self.retrieve_with_scores(question, top_k)]

    def retrieve_with_scores(self, question: str, top_k: int) -> list[tuple[Document, float]]:
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client import QdrantClient
        except Exception:
            return self._fallback_documents_with_scores(question, top_k)

        api_key = self.settings.novita_api_key or self.settings.openai_api_key
        if not api_key:
            return self._fallback_documents_with_scores(question, top_k)

        embedding = OpenAIEmbeddings(
            api_key=api_key,
            base_url=self.settings.novita_base_url or self.settings.openai_base_url or None,
            model=self.settings.embedding_model,
        )
        client = QdrantClient(url=self.settings.qdrant_url)
        store = QdrantVectorStore(
            client=client,
            collection_name=self.settings.qdrant_collection,
            embedding=embedding,
        )
        return store.similarity_search_with_score(question, k=top_k)

    def _fallback_documents(self, question: str, top_k: int) -> list[Document]:
        return [doc for doc, _ in self._fallback_documents_with_scores(question, top_k)]

    def _fallback_documents_with_scores(self, question: str, top_k: int) -> list[tuple[Document, float]]:
        local = LocalRetriever(self.settings.rag_doc_path)
        return [
            (
                Document(page_content=chunk.content, metadata={"chunk_id": chunk.chunk_id, "score": score}),
                score,
            )
            for chunk, score in local.query(question, top_k=top_k)
        ]


class VectorSyncService:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.session = session

    def upsert_chunks(self, chunk_ids: list[str]) -> int:
        total = 0
        for chunk_id in chunk_ids:
            total += self.upsert_chunk(chunk_id)
        return total

    def upsert_chunk(self, chunk_id: str) -> int:
        payload = self._load_chunk_by_id(chunk_id)
        if payload is None:
            return 0
        return 1 if self._upsert_point(payload) else 0

    def delete_chunk(self, chunk_id: str) -> int:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qm
        except Exception:
            return 0
        client = QdrantClient(url=self.settings.qdrant_url)
        client.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=qm.PointIdsList(points=[chunk_id]),
        )
        return 1

    def sync_vector_event(self, event: dict[str, Any]) -> int:
        action = str(event.get("action", ""))
        entity_type = str(event.get("entity_type", ""))
        entity_id = str(event.get("entity_id", ""))
        payload = (event.get("payload") or {})

        if action == "deleted":
            if entity_type == "chunk":
                return self.delete_chunk(entity_id)
            return self.delete_chunk(f"{entity_type}:{entity_id}")

        if entity_type == "chunk":
            if payload:
                chunk = self._chunk_from_payload(entity_id, payload)
                return 1 if self._upsert_point(chunk) else 0
            return self.upsert_chunk(entity_id)

        if entity_type in {"post", "symbol", "report", "report_data", "market_mention"}:
            return self.upsert_chunk(f"{entity_type}:{entity_id}")

        if action == "reindex":
            if payload.get("chunk_ids"):
                chunk_ids = [str(x) for x in payload.get("chunk_ids", [])]
                return self.upsert_chunks(chunk_ids)
            return self.upsert_chunk(f"{entity_type}:{entity_id}")
        return 0

    def _upsert_point(self, chunk: ChunkPayload) -> bool:
        try:
            from langchain_openai import OpenAIEmbeddings
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qm
        except Exception:
            return False

        api_key = self.settings.novita_api_key or self.settings.openai_api_key
        if not api_key:
            return False

        content_hash = compute_content_hash(chunk.content)
        metadata = dict(chunk.metadata)
        metadata["content_hash"] = content_hash
        metadata["chunk_hash"] = compute_chunk_hash(chunk.content, metadata)

        client = QdrantClient(url=self.settings.qdrant_url)
        existing = client.retrieve(
            collection_name=self.settings.qdrant_collection,
            ids=[chunk.chunk_id],
            with_payload=True,
            with_vectors=False,
        )
        if existing:
            existing_hash = (existing[0].payload or {}).get("chunk_hash")
            if existing_hash == metadata["chunk_hash"]:
                return False

        embedding = OpenAIEmbeddings(
            api_key=api_key,
            base_url=self.settings.novita_base_url or self.settings.openai_base_url or None,
            model=self.settings.embedding_model,
        )
        vector = embedding.embed_query(chunk.content)
        point = qm.PointStruct(
            id=chunk.chunk_id,
            vector=vector,
            payload={
                **metadata,
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
            },
        )
        client.upsert(collection_name=self.settings.qdrant_collection, points=[point], wait=True)
        return True

    def _chunk_from_payload(self, chunk_id: str, payload: dict[str, Any]) -> ChunkPayload:
        content = str(payload.get("content", "")).strip()
        meta = {
            "document_id": payload.get("document_id"),
            "post_id": payload.get("post_id"),
            "ticker_list": payload.get("ticker_list"),
            "source_type": payload.get("source_type", "external"),
            "title": payload.get("title"),
            "section_path": payload.get("section_path"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
        }
        return ChunkPayload(chunk_id=str(chunk_id), content=content, metadata=meta)

    def _load_chunk_by_id(self, chunk_id: str) -> ChunkPayload | None:
        if ":" not in chunk_id:
            return None
        entity_type, raw_id = chunk_id.split(":", 1)
        if entity_type == "post":
            rows = self._fetch_rows(
                """
                SELECT p.post_id, p.fireant_post_id, p.title, p.content, p.published_at,
                       COALESCE(string_agg(DISTINCT ts.symbol_ticker, ','), '') AS tickers
                FROM posts p
                LEFT JOIN tagged_symbols ts ON ts.post_id = p.post_id
                WHERE p.post_id = :id
                GROUP BY p.post_id, p.fireant_post_id, p.title, p.content, p.published_at
                """,
                {"id": int(raw_id)},
            )
            if not rows:
                return None
            row = rows[0]
            content = f"{row.get('title') or ''}\n\n{row.get('content') or ''}".strip()
            return ChunkPayload(
                chunk_id=chunk_id,
                content=content,
                metadata={
                    "document_id": f"post:{row['post_id']}",
                    "post_id": row["post_id"],
                    "ticker_list": [t for t in str(row.get("tickers") or "").split(",") if t],
                    "source_type": "post",
                    "title": row.get("title"),
                    "section_path": "post/body",
                    "created_at": row.get("published_at"),
                    "updated_at": row.get("published_at"),
                },
            )
        if entity_type == "symbol":
            rows = self._fetch_rows(
                """
                SELECT ticker, company_name, exchange, sector, industry, short_industry, cap_ratio
                FROM symbols WHERE ticker = :id
                """,
                {"id": raw_id},
            )
            if not rows:
                return None
            row = rows[0]
            content = (
                f"Ticker: {row.get('ticker')}\nCompany: {row.get('company_name')}\n"
                f"Exchange: {row.get('exchange')}\nSector: {row.get('sector')}\n"
                f"Industry: {row.get('industry')}\nShortIndustry: {row.get('short_industry')}\n"
                f"CapRatio: {row.get('cap_ratio')}"
            )
            return ChunkPayload(
                chunk_id=chunk_id,
                content=content,
                metadata={
                    "document_id": f"symbol:{row['ticker']}",
                    "post_id": None,
                    "ticker_list": [row["ticker"]],
                    "source_type": "symbol",
                    "title": row.get("company_name"),
                    "section_path": "symbol/profile",
                    "created_at": None,
                    "updated_at": None,
                },
            )
        if entity_type == "report_data":
            rows = self._fetch_rows(
                """
                SELECT rd.id, rd.year, rd.quarter, rd.value, r.id AS report_id, r.name, r.symbol_ticker
                FROM report_data rd
                JOIN reports r ON r.id = rd.report_id
                WHERE rd.id = :id
                """,
                {"id": int(raw_id)},
            )
            if not rows:
                return None
            row = rows[0]
            content = (
                f"Ticker: {row.get('symbol_ticker')}\nReport: {row.get('name')}\n"
                f"Year: {row.get('year')}\nQuarter: {row.get('quarter')}\nValue: {row.get('value')}"
            )
            return ChunkPayload(
                chunk_id=chunk_id,
                content=content,
                metadata={
                    "document_id": f"report:{row['report_id']}",
                    "post_id": None,
                    "ticker_list": [row.get("symbol_ticker")] if row.get("symbol_ticker") else [],
                    "source_type": "report_data",
                    "title": row.get("name"),
                    "section_path": "report/data",
                    "created_at": None,
                    "updated_at": None,
                },
            )
        return None

    def _fetch_rows(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        rows = self.session.execute(text(sql), params).fetchall()
        return [self._normalize_row(dict(r._mapping)) for r in rows]

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                out[key] = float(value)
            elif isinstance(value, (datetime, date)):
                out[key] = value.isoformat()
            else:
                out[key] = value
        return out
