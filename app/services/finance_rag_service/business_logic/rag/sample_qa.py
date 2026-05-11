from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import redis
from common.config.finance_rag import Settings
from common.orm.models import RagQueryAnalytics, RagQueryCache, RagSampleAnswer, RagSampleQuestion
from loguru import logger
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

QUESTION_CLEAN_RE = re.compile(r"[^a-z0-9\s]")
SPACES_RE = re.compile(r"\s+")
TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")


def normalize_question(question: str) -> str:
    q = question.strip()
    tickers = sorted(set(TICKER_RE.findall(q.upper())))
    q = q.lower()
    q = QUESTION_CLEAN_RE.sub(" ", q)
    q = SPACES_RE.sub(" ", q).strip()
    if tickers:
        q = f"{q} | tickers:{','.join(tickers)}"
    return q


def compute_question_hash(normalized_question: str) -> str:
    return hashlib.sha256(normalized_question.encode("utf-8")).hexdigest()


def is_answer_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    now = datetime.now(UTC)
    if expires_at.tzinfo is None:
        return expires_at.replace(tzinfo=UTC) <= now
    return expires_at <= now


class SampleQAMatcher:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def match_sample_question(self, query: str) -> RagSampleQuestion | None:
        norm = normalize_question(query)
        exact_stmt = (
            select(RagSampleQuestion)
            .where(
                RagSampleQuestion.normalized_question == norm,
                RagSampleQuestion.is_active.is_(True),
            )
            .order_by(desc(RagSampleQuestion.priority), desc(RagSampleQuestion.updated_at))
            .limit(1)
        )
        exact = self.session.execute(exact_stmt).scalar_one_or_none()
        if exact:
            return exact

        like_prefix = norm[:120]
        fuzzy_stmt = (
            select(RagSampleQuestion)
            .where(
                RagSampleQuestion.normalized_question.ilike(f"%{like_prefix}%"),
                RagSampleQuestion.is_active.is_(True),
            )
            .order_by(desc(RagSampleQuestion.priority), desc(RagSampleQuestion.updated_at))
            .limit(20)
        )
        candidates = self.session.execute(fuzzy_stmt).scalars().all()
        for candidate in candidates:
            if self._token_overlap(norm, candidate.normalized_question) >= 0.7:
                return candidate
        return None

    def load_sample_answer(self, question_id: int) -> RagSampleAnswer | None:
        stmt = (
            select(RagSampleAnswer)
            .where(RagSampleAnswer.sample_question_id == question_id)
            .order_by(desc(RagSampleAnswer.updated_at))
            .limit(1)
        )
        answer = self.session.execute(stmt).scalar_one_or_none()
        if answer is None:
            return None
        if is_answer_expired(answer.expires_at):
            return None
        return answer

    def preload_hot_answers(self, limit: int = 200) -> int:
        stmt = (
            select(RagSampleQuestion, RagSampleAnswer)
            .join(RagSampleAnswer, RagSampleAnswer.sample_question_id == RagSampleQuestion.id)
            .where(RagSampleQuestion.is_active.is_(True))
            .order_by(desc(RagSampleQuestion.priority), desc(RagSampleAnswer.updated_at))
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        loaded = 0
        for q, a in rows:
            if is_answer_expired(a.expires_at):
                continue
            norm = q.normalized_question
            q_hash = compute_question_hash(norm)
            key = f"rag:sample_answer:{q_hash}"
            ttl = int((a.expires_at - datetime.now(UTC)).total_seconds()) if a.expires_at else 86400
            ttl = max(ttl, 300)
            payload = {
                "question_id": q.id,
                "answer_id": a.id,
                "answer": a.answer,
                "citations": a.citations or [],
                "context_refs": a.context_refs or {},
                "model_name": a.model_name,
                "version": a.version,
                "prompt_version": a.prompt_version,
                "embedding_version": a.embedding_version,
                "summary_version": a.summary_version,
            }
            self.redis_client.setex(key, ttl, json.dumps(payload, ensure_ascii=False, default=str))
            loaded += 1
        logger.info("Preloaded sample hot answers loaded={loaded}", loaded=loaded)
        return loaded

    def get_hot_answer(self, query: str) -> dict[str, Any] | None:
        norm = normalize_question(query)
        q_hash = compute_question_hash(norm)
        val = self.redis_client.get(f"rag:sample_answer:{q_hash}")
        if not val:
            return None
        return json.loads(val)

    def get_query_cache(self, query: str) -> RagQueryCache | None:
        norm = normalize_question(query)
        stmt = (
            select(RagQueryCache)
            .where(RagQueryCache.normalized_query == norm)
            .order_by(desc(RagQueryCache.updated_at))
            .limit(1)
        )
        cached = self.session.execute(stmt).scalar_one_or_none()
        if cached and not is_answer_expired(cached.expires_at):
            return cached
        return None

    def upsert_query_cache(
        self,
        query: str,
        answer: str,
        citations: list[dict[str, Any]] | None,
        model_name: str | None,
        ttl_seconds: int = 3600,
    ) -> None:
        norm = normalize_question(query)
        q_hash = compute_question_hash(norm)
        now = datetime.now(UTC)
        expires = now + timedelta(seconds=ttl_seconds)

        stmt = select(RagQueryCache).where(RagQueryCache.normalized_query == norm).limit(1)
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            row = RagQueryCache(
                normalized_query=norm,
                question_hash=q_hash,
                answer=answer,
                citations=citations,
                model_name=model_name,
                prompt_version=self.settings.prompt_version,
                embedding_version=self.settings.embedding_version,
                generated_at=now,
                updated_at=now,
                expires_at=expires,
            )
            self.session.add(row)
        else:
            row.answer = answer
            row.citations = citations
            row.model_name = model_name
            row.prompt_version = self.settings.prompt_version
            row.embedding_version = self.settings.embedding_version
            row.updated_at = now
            row.expires_at = expires

    def track_query_analytics(self, query: str, latency_ms: float) -> None:
        norm = normalize_question(query)
        now = datetime.now(UTC)
        stmt = select(RagQueryAnalytics).where(RagQueryAnalytics.normalized_query == norm).limit(1)
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            row = RagQueryAnalytics(
                normalized_query=norm,
                hit_count=1,
                avg_latency_ms=latency_ms,
                last_seen_at=now,
                created_at=now,
            )
            self.session.add(row)
            return
        total = row.avg_latency_ms * row.hit_count + latency_ms
        row.hit_count += 1
        row.avg_latency_ms = total / row.hit_count
        row.last_seen_at = now

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        ta = set(a.split())
        tb = set(b.split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / max(1, len(ta))
