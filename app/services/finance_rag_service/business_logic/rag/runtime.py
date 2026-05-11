from __future__ import annotations

from time import perf_counter

from business_logic.rag.chat_history import ChatHistoryService
from business_logic.rag.citation import CitationGroundingValidator
from business_logic.rag.langgraph_flow import FinanceRagFlow
from business_logic.rag.sample_qa import SampleQAMatcher
from business_logic.rag.schemas import RagQueryResponse, RagSource
from common.config.finance_rag import Settings
from common.orm.db import session_scope
from loguru import logger


def run_rag_query(
    question: str,
    top_k: int,
    settings: Settings,
    *,
    conversation_id: str = "default",
    user_id: str | None = None,
) -> RagQueryResponse:
    started = perf_counter()
    with session_scope() as session:
        matcher = SampleQAMatcher(session=session, settings=settings)
        history = ChatHistoryService(session=session)
        history.append_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=question,
            metadata_json={"route_stage": "received"},
        )

        hot = matcher.get_hot_answer(question)
        if hot:
            latency_ms = (perf_counter() - started) * 1000
            matcher.track_query_analytics(question, latency_ms)
            logger.info(
                "rag_query route=redis_hot cache_hit=true sample_hit=true retrieval_hit=false latency_ms={latency:.2f} reused_answer=true",
                latency=latency_ms,
            )
            answer_text = str(hot.get("answer", ""))
            history.append_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=answer_text,
                sources=[{"chunk_id": 1, "score": 1.0, "content": "sample_hot_cache"}],
                metadata_json={"route_stage": "redis_hot", "latency_ms": round(latency_ms, 2)},
            )
            return RagQueryResponse(
                question=question,
                answer=answer_text,
                sources=[RagSource(chunk_id=1, score=1.0, content="sample_hot_cache")],
            )

        sample_q = matcher.match_sample_question(question)
        if sample_q:
            sample_a = matcher.load_sample_answer(sample_q.id)
            if sample_a:
                latency_ms = (perf_counter() - started) * 1000
                matcher.track_query_analytics(question, latency_ms)
                logger.info(
                    "rag_query route=sample_db cache_hit=false sample_hit=true retrieval_hit=false latency_ms={latency:.2f} reused_answer=true",
                    latency=latency_ms,
                )
                history.append_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="assistant",
                    content=sample_a.answer,
                    sources=[{"chunk_id": 1, "score": 1.0, "content": "sample_db"}],
                    metadata_json={"route_stage": "sample_db", "latency_ms": round(latency_ms, 2)},
                )
                return RagQueryResponse(
                    question=question,
                    answer=sample_a.answer,
                    sources=[RagSource(chunk_id=1, score=1.0, content="sample_db")],
                )

        cached = matcher.get_query_cache(question)
        if cached:
            latency_ms = (perf_counter() - started) * 1000
            matcher.track_query_analytics(question, latency_ms)
            logger.info(
                "rag_query route=query_cache cache_hit=true sample_hit=false retrieval_hit=false latency_ms={latency:.2f} reused_answer=true",
                latency=latency_ms,
            )
            history.append_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=cached.answer,
                sources=[{"chunk_id": 1, "score": 1.0, "content": "query_cache"}],
                metadata_json={"route_stage": "query_cache", "latency_ms": round(latency_ms, 2)},
            )
            return RagQueryResponse(
                question=question,
                answer=cached.answer,
                sources=[RagSource(chunk_id=1, score=1.0, content="query_cache")],
            )

        flow = FinanceRagFlow(settings)
        state = flow.run(question, top_k)
        answer = state.get("answer", "")
        source_refs = state.get("source_refs", [])
        sources = [
            RagSource(
                chunk_id=int(ref.get("chunk_id") or idx + 1),
                score=float(ref.get("score") or 1.0),
                content=state.get("vector_contexts", [])[idx]
                if idx < len(state.get("vector_contexts", []))
                else "context",
            )
            for idx, ref in enumerate(
                source_refs
                or [{"chunk_id": i + 1} for i, _ in enumerate(state.get("vector_contexts", []))]
            )
        ]
        validation = CitationGroundingValidator().validate(
            answer=answer,
            sources=[{"chunk_id": s.chunk_id, "score": s.score} for s in sources],
        )
        if not validation.ok:
            answer = f"{answer}\n\nSources:\n" + "\n".join(
                [f"[{s.chunk_id}] score={s.score}" for s in sources[:5]]
            )
        matcher.upsert_query_cache(
            query=question,
            answer=answer,
            citations=[{"chunk_id": s.chunk_id, "score": s.score} for s in sources],
            model_name=settings.novita_model or settings.openai_model,
            ttl_seconds=3600,
        )
        latency_ms = (perf_counter() - started) * 1000
        matcher.track_query_analytics(question, latency_ms)
        logger.info(
            "rag_query route=langgraph cache_hit=false sample_hit=false retrieval_hit=true latency_ms={latency:.2f} reused_answer=false",
            latency=latency_ms,
        )
        history.append_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=answer,
            sources=[{"chunk_id": s.chunk_id, "score": s.score, "content": s.content[:300]} for s in sources[:10]],
            metadata_json={"route_stage": "final", "latency_ms": round(latency_ms, 2)},
        )
        return RagQueryResponse(question=question, answer=answer, sources=sources)
