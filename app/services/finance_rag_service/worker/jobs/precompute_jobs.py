from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from time import perf_counter

import redis
from common.config.finance_rag import get_settings
from common.orm.db import session_scope
from common.orm.models import (
    RagConversationSummary,
    RagQueryAnalytics,
    RagQueryCache,
    RagSampleAnswer,
    RagSampleQuestion,
)
from loguru import logger
from sqlalchemy import delete, desc, select

from rag.graph_store import GraphContextProvider
from rag.langgraph_flow import FinanceRagFlow
from rag.sample_qa import SampleQAMatcher, compute_question_hash, normalize_question


def _redis() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def conversation_summarization_worker(limit: int = 100) -> dict:
    started = perf_counter()
    # Placeholder pipeline: summarize cached query answers into conversation summaries by normalized query
    with session_scope() as session:
        stmt = select(RagQueryCache).order_by(desc(RagQueryCache.updated_at)).limit(limit)
        rows = session.execute(stmt).scalars().all()
        for row in rows:
            summary = row.answer[:600]
            cs = RagConversationSummary(
                conversation_id=f"query:{row.question_hash}",
                user_id="system",
                summary=summary,
                important_tickers=[],
                important_entities={"normalized_query": row.normalized_query},
                summary_version=get_settings().summary_version,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            session.add(cs)
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=conversation_summarization_worker latency_ms={latency:.2f}", latency=duration_ms)
    return {"status": "ok", "worker_name": "conversation_summarization_worker", "duration_ms": round(duration_ms, 2)}


def popular_query_precompute_worker(limit: int = 50) -> dict:
    started = perf_counter()
    settings = get_settings()
    flow = FinanceRagFlow(settings)
    cache = _redis()
    processed = 0
    with session_scope() as session:
        stmt = select(RagQueryAnalytics).order_by(desc(RagQueryAnalytics.hit_count)).limit(limit)
        rows = session.execute(stmt).scalars().all()
        for row in rows:
            state = flow.run(row.normalized_query, top_k=min(4, settings.max_context_chunks))
            answer = state.get("answer", "")
            q_hash = compute_question_hash(row.normalized_query)
            key = f"rag:popular_query:{q_hash}"
            cache.setex(key, 3600, json.dumps({"answer": answer, "query": row.normalized_query}, ensure_ascii=False))
            processed += 1
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=popular_query_precompute_worker processed={processed} latency_ms={latency:.2f}", processed=processed, latency=duration_ms)
    return {"status": "ok", "processed": processed, "worker_name": "popular_query_precompute_worker", "duration_ms": round(duration_ms, 2)}


def symbol_profile_precompute_worker(limit: int = 200) -> dict:
    started = perf_counter()
    cache = _redis()
    with session_scope() as session:
        rows = session.execute(select(RagSampleQuestion).where(RagSampleQuestion.is_active.is_(True)).limit(limit)).scalars().all()
        for q in rows:
            tickers = q.tickers or []
            if not tickers:
                continue
            cache.setex(f"rag:market_summary:{tickers[0]}", 3600, q.question)
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=symbol_profile_precompute_worker latency_ms={latency:.2f}", latency=duration_ms)
    return {"status": "ok", "worker_name": "symbol_profile_precompute_worker", "duration_ms": round(duration_ms, 2)}


def market_summary_precompute_worker(limit: int = 100) -> dict:
    started = perf_counter()
    settings = get_settings()
    flow = FinanceRagFlow(settings)
    cache = _redis()
    tickers = ["VNINDEX", "VN30", "HNX", "UPCOM"][:limit]
    for ticker in tickers:
        q = f"market summary for {ticker}"
        state = flow.run(q, top_k=min(4, settings.max_context_chunks))
        cache.setex(f"rag:market_summary:{ticker}", 1800, state.get("answer", ""))
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=market_summary_precompute_worker latency_ms={latency:.2f}", latency=duration_ms)
    return {"status": "ok", "worker_name": "market_summary_precompute_worker", "duration_ms": round(duration_ms, 2)}


def stale_cache_cleanup_worker(db_limit: int = 1000) -> dict:
    started = perf_counter()
    cache = _redis()
    # Redis cleanup by pattern (best effort)
    for pattern in ["rag:sample_answer:*", "rag:popular_query:*", "rag:market_summary:*", "rag:graph_context:*"]:
        for key in cache.scan_iter(match=pattern, count=1000):
            ttl = cache.ttl(key)
            if ttl == -1:
                cache.expire(key, 3600)

    now = datetime.now(UTC)
    with session_scope() as session:
        session.execute(delete(RagQueryCache).where(RagQueryCache.expires_at.is_not(None), RagQueryCache.expires_at < now))
        session.execute(delete(RagSampleAnswer).where(RagSampleAnswer.expires_at.is_not(None), RagSampleAnswer.expires_at < now))
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=stale_cache_cleanup_worker latency_ms={latency:.2f}", latency=duration_ms)
    return {"status": "ok", "worker_name": "stale_cache_cleanup_worker", "duration_ms": round(duration_ms, 2)}


def sample_qa_precompute_worker(limit: int = 200) -> dict:
    started = perf_counter()
    loaded = 0
    with session_scope() as session:
        matcher = SampleQAMatcher(session=session, settings=get_settings())
        loaded = matcher.preload_hot_answers(limit=limit)
        # refresh expired sample answers with query-cache fallback text
        stmt = select(RagSampleQuestion).where(RagSampleQuestion.is_active.is_(True)).limit(limit)
        for q in session.execute(stmt).scalars().all():
            ans = matcher.load_sample_answer(q.id)
            if ans is None:
                placeholder = RagSampleAnswer(
                    sample_question_id=q.id,
                    answer=f"Precompute pending for: {q.question}",
                    citations=[],
                    context_refs={},
                    model_name=get_settings().novita_model,
                    version="v1",
                    prompt_version=get_settings().prompt_version,
                    embedding_version=get_settings().embedding_version,
                    summary_version=get_settings().summary_version,
                    generated_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC) + timedelta(hours=6),
                    updated_at=datetime.now(UTC),
                )
                session.add(placeholder)
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=sample_qa_precompute_worker loaded={loaded} latency_ms={latency:.2f}", loaded=loaded, latency=duration_ms)
    return {"status": "ok", "worker_name": "sample_qa_precompute_worker", "loaded": loaded, "duration_ms": round(duration_ms, 2)}


def retrieval_cache_refresh_worker(limit: int = 100) -> dict:
    started = perf_counter()
    settings = get_settings()
    flow = FinanceRagFlow(settings)
    cache = _redis()
    refreshed = 0
    with session_scope() as session:
        rows = session.execute(select(RagQueryAnalytics).order_by(desc(RagQueryAnalytics.hit_count)).limit(limit)).scalars().all()
        for row in rows:
            state = flow.run(row.normalized_query, top_k=min(4, settings.max_context_chunks))
            q_hash = compute_question_hash(row.normalized_query)
            cache.setex(f"rag:popular_query:{q_hash}", 3600, json.dumps({"answer": state.get("answer", "")}, ensure_ascii=False))
            refreshed += 1
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=retrieval_cache_refresh_worker refreshed={refreshed} latency_ms={latency:.2f}", refreshed=refreshed, latency=duration_ms)
    return {"status": "ok", "worker_name": "retrieval_cache_refresh_worker", "refreshed": refreshed, "duration_ms": round(duration_ms, 2)}


def graph_context_precompute_worker(limit: int = 200) -> dict:
    started = perf_counter()
    settings = get_settings()
    graph = GraphContextProvider(settings)
    cache = _redis()
    with session_scope() as session:
        rows = session.execute(select(RagSampleQuestion).where(RagSampleQuestion.is_active.is_(True)).limit(limit)).scalars().all()
        for q in rows:
            tickers = q.tickers or []
            if not tickers:
                continue
            ticker = tickers[0]
            snippets = graph.fetch_context(ticker, limit=10)
            cache.setex(f"rag:graph_context:{ticker}", 1800, json.dumps({"ticker": ticker, "snippets": snippets}, ensure_ascii=False))
    duration_ms = (perf_counter() - started) * 1000
    logger.info("worker_name=graph_context_precompute_worker latency_ms={latency:.2f}", latency=duration_ms)
    return {"status": "ok", "worker_name": "graph_context_precompute_worker", "duration_ms": round(duration_ms, 2)}
