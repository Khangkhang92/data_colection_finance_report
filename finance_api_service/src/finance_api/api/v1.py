from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status

from finance_api.config import Settings, get_settings
from finance_api.jobs import (
    job_manager,
    run_company_details_sync,
    run_finance_statements_sync,
    run_history_prices_sync,
    run_market_mentions_sync,
    run_posts_sync,
    run_session_quotes_sync,
    run_symbols_sync,
)
from finance_api.schemas import (
    CompanyDetailsSyncRequest,
    FinanceStatementsSyncRequest,
    HistoryPricesSyncRequest,
    JobAcceptedResponse,
    JobStatusResponse,
    MarketMentionsSyncRequest,
    PostsSyncRequest,
    SessionQuotesSyncRequest,
    SymbolsSyncRequest,
    SyncResponse,
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


@router.post(
    "/webhooks/posts/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_posts(
    request: PostsSyncRequest,
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "posts_sync",
        lambda: run_posts_sync(request),
        dedupe_key="posts_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="Posts sync job accepted",
    )


@router.post(
    "/webhooks/finance-statements/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_finance_statements(
    settings: Settings = Depends(get_settings),
    ) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "finance_statements_sync",
        run_finance_statements_sync,
        dedupe_key="finance_statements_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="Finance statements sync job accepted",
    )


@router.post(
    "/webhooks/company-details/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_company_details(
    request: CompanyDetailsSyncRequest = Body(default_factory=CompanyDetailsSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "company_details_sync",
        lambda: run_company_details_sync(request),
        dedupe_key="company_details_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="Company details sync job accepted",
    )


@router.post(
    "/webhooks/symbols/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_symbols(
    request: SymbolsSyncRequest = Body(default_factory=SymbolsSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "symbols_sync",
        lambda: run_symbols_sync(request),
        dedupe_key="symbols_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="Symbols sync job accepted",
    )


@router.post(
    "/webhooks/market-mentions/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_market_mentions(
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "market_mentions_sync",
        run_market_mentions_sync,
        dedupe_key="market_mentions_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="Market mentions sync job accepted",
    )


@router.post(
    "/webhooks/session-quotes/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_session_quotes(
    request: SessionQuotesSyncRequest = Body(default_factory=SessionQuotesSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "session_quotes_sync",
        lambda: run_session_quotes_sync(request),
        dedupe_key="session_quotes_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="Session quotes sync job accepted",
    )


@router.post(
    "/webhooks/history-prices/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_history_prices(
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job, deduplicated = job_manager.enqueue(
        "history_prices_sync",
        run_history_prices_sync,
        dedupe_key="history_prices_sync",
    )
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=deduplicated,
        message="History prices sync job accepted",
    )
