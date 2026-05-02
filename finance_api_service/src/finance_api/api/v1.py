from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status

from finance_api.config import Settings, get_settings
from finance_api.jobs import (
    enqueue_job,
    get_job,
)
from finance_api.schemas import (
    CompanyDetailsSyncRequest,
    JobAcceptedResponse,
    JobStatusResponse,
    PostsSyncRequest,
    SessionQuotesSyncRequest,
    SymbolsSyncRequest,
)
router = APIRouter(prefix="/fireant_data", tags=["fireant-data"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = get_job(job_id)
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
    job = enqueue_job("posts_sync", request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
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
    job = enqueue_job("finance_statements_sync", {})
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
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
    job = enqueue_job("company_details_sync", request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
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
    job = enqueue_job("symbols_sync", request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
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
    job = enqueue_job("market_mentions_sync", {})
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
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
    job = enqueue_job("session_quotes_sync", request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
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
    job = enqueue_job("history_prices_sync", {})
    return JobAcceptedResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        status=job.status,
        deduplicated=False,
        message="History prices sync job accepted",
    )
