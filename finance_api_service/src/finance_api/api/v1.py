from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status

from finance_api.config import Settings, get_settings
from finance_api.jobs import enqueue_job
from finance_api.schemas import (
    CompanyDetailsSyncRequest,
    ExtendedInstrumentsSyncRequest,
    FundamentalsSyncRequest,
    HistoryPricesSyncRequest,
    IndustriesSyncRequest,
    JobAcceptedResponse,
    PostsSyncRequest,
    SessionQuotesSyncRequest,
    SymbolsSyncRequest,
)
router = APIRouter(prefix="/fireant_data", tags=["fireant-data"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.post(
    "/webhooks/posts/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_posts(
    request: PostsSyncRequest,
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job_name = "posts_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
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
    job_name = "finance_statements_sync"
    enqueue_job(job_name, {})
    return JobAcceptedResponse(
        job_name=job_name,
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
    job_name = "company_details_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
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
    job_name = "symbols_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
        message="Symbols sync job accepted",
    )


@router.post(
    "/webhooks/industries/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_industries(
    request: IndustriesSyncRequest = Body(default_factory=IndustriesSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job_name = "industries_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
        message="Industries sync job accepted",
    )


@router.post(
    "/webhooks/market-mentions/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_market_mentions(
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job_name = "market_mentions_sync"
    enqueue_job(job_name, {})
    return JobAcceptedResponse(
        job_name=job_name,
        message="Market mentions sync job accepted",
    )


@router.post(
    "/webhooks/fundamentals/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_fundamentals(
    request: FundamentalsSyncRequest = Body(default_factory=FundamentalsSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job_name = "fundamentals_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
        message="Fundamentals sync job accepted",
    )


@router.post(
    "/webhooks/extended-instruments/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_extended_instruments(
    request: ExtendedInstrumentsSyncRequest = Body(default_factory=ExtendedInstrumentsSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job_name = "extended_instruments_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
        message="Extended instruments sync job accepted",
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
    job_name = "session_quotes_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
        message="Session quotes sync job accepted",
    )


@router.post(
    "/webhooks/history-prices/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_history_prices(
    request: HistoryPricesSyncRequest = Body(default_factory=HistoryPricesSyncRequest),
    settings: Settings = Depends(get_settings),
) -> JobAcceptedResponse:
    job_name = "history_prices_sync"
    enqueue_job(job_name, request.model_dump(mode="json"))
    return JobAcceptedResponse(
        job_name=job_name,
        message="History prices sync job accepted",
    )
