from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from common.config.finance_api import Settings, get_settings
from common.config.finance_rag import get_settings as get_rag_settings
from business_logic.jobs import (
    job_manager,
    run_company_details_sync,
    run_finance_statements_sync,
    run_history_prices_sync,
    run_market_mentions_sync,
    run_posts_sync,
    run_session_quotes_sync,
    run_symbols_sync,
)
from rag.runtime import run_rag_query
from rag.chat_history import ChatHistoryService
from rag.chunk_checker import check_chunks
from rag.schemas import (
    RagChatHistoryResponse,
    RagChatMessage,
    RagChatRequest,
    ChunkCheckRequest,
    ChunkCheckResponse,
    RagQueryRequest,
    RagQueryResponse,
)
from common.orm.db import session_scope
from common.orm.schemas import (
    CompanyDetailsSyncRequest,
    JobAcceptedResponse,
    JobStatusResponse,
    SessionQuotesSyncRequest,
    SymbolsSyncRequest,
    PostsSyncRequest,
)

router = APIRouter(prefix="/fireant_data", tags=["fireant-data"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobStatusResponse(**job.__dict__)


@router.post("/webhooks/posts/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_posts(request: PostsSyncRequest, settings: Settings = Depends(get_settings)) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("posts_sync", lambda: run_posts_sync(request), dedupe_key="posts_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="Posts sync job accepted")


@router.post("/webhooks/finance-statements/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_finance_statements(settings: Settings = Depends(get_settings)) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("finance_statements_sync", run_finance_statements_sync, dedupe_key="finance_statements_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="Finance statements sync job accepted")


@router.post("/webhooks/company-details/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_company_details(
    request: CompanyDetailsSyncRequest = Body(default_factory=CompanyDetailsSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("company_details_sync", lambda: run_company_details_sync(request), dedupe_key="company_details_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="Company details sync job accepted")


@router.post("/webhooks/symbols/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_symbols(
    request: SymbolsSyncRequest = Body(default_factory=SymbolsSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("symbols_sync", lambda: run_symbols_sync(request), dedupe_key="symbols_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="Symbols sync job accepted")


@router.post("/webhooks/market-mentions/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_market_mentions(settings: Settings = Depends(get_settings)) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("market_mentions_sync", run_market_mentions_sync, dedupe_key="market_mentions_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="Market mentions sync job accepted")


@router.post("/webhooks/session-quotes/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_session_quotes(
    request: SessionQuotesSyncRequest = Body(default_factory=SessionQuotesSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("session_quotes_sync", lambda: run_session_quotes_sync(request), dedupe_key="session_quotes_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="Session quotes sync job accepted")


@router.post("/webhooks/history-prices/sync", response_model=JobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_history_prices(settings: Settings = Depends(get_settings)) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue("history_prices_sync", run_history_prices_sync, dedupe_key="history_prices_sync")
    return JobAcceptedResponse(job_id=job.job_id, job_name=job.job_name, status=job.status, deduplicated=deduplicated, message="History prices sync job accepted")


@router.post("/rag/query", response_model=RagQueryResponse)
def rag_query(payload: RagQueryRequest):
    rag_settings = get_rag_settings()
    top_k = min(payload.top_k, rag_settings.max_context_chunks)
    return run_rag_query(
        question=payload.question,
        top_k=top_k,
        settings=rag_settings,
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
    )


@router.post("/rag/chat", response_model=RagQueryResponse)
def rag_chat(payload: RagChatRequest):
    rag_settings = get_rag_settings()
    top_k = min(payload.top_k, rag_settings.max_context_chunks)
    return run_rag_query(
        question=payload.message,
        top_k=top_k,
        settings=rag_settings,
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
    )


@router.get("/rag/chat/history", response_model=RagChatHistoryResponse)
def rag_chat_history(
    conversation_id: str = Query(..., min_length=1, max_length=128),
    limit: int = Query(default=50, ge=1, le=200),
) -> RagChatHistoryResponse:
    with session_scope() as session:
        rows = ChatHistoryService(session=session).list_recent(conversation_id=conversation_id, limit=limit)
        messages = [
            RagChatMessage(
                id=int(row.id),
                conversation_id=row.conversation_id,
                user_id=row.user_id,
                role=row.role,
                content=row.content,
                sources=row.sources,
                metadata_json=row.metadata_json,
                created_at=row.created_at.isoformat(),
            )
            for row in rows
        ]
        return RagChatHistoryResponse(conversation_id=conversation_id, messages=messages)


@router.post("/rag/chunks/check", response_model=ChunkCheckResponse)
def rag_check_chunks(payload: ChunkCheckRequest) -> ChunkCheckResponse:
    try:
        count, chunks, next_cursor = check_chunks(
            table=payload.table,
            filters=payload.filters,
            limit=payload.limit,
            keyword=payload.keyword,
            cursor=payload.cursor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChunkCheckResponse(table=payload.table, count=count, chunks=chunks, next_cursor=next_cursor)
