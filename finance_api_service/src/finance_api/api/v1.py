from __future__ import annotations

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from finance_api.api.deps import get_client
from finance_api.clients import ApiClient
from finance_api.config import Settings, get_settings
from finance_api.db import get_session
from finance_api.schemas import (
    CompanyDetailsSyncRequest,
    FinanceStatementsSyncRequest,
    HistoryPricesSyncRequest,
    MarketMentionsSyncRequest,
    PostsSyncRequest,
    SessionQuotesSyncRequest,
    SymbolsSyncRequest,
    SyncResponse,
)
from finance_api.services.company import CompanyService
from finance_api.services.finance_report import FinanceStatementService
from finance_api.services.market import MarketService
from finance_api.services.posts import PostsService
from finance_api.services.symbols import SymbolService

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.post("/webhooks/posts/sync", response_model=SyncResponse)
def sync_posts(
    request: PostsSyncRequest,
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return PostsService(settings, client, session).sync(request)


@router.post("/webhooks/finance-statements/sync", response_model=SyncResponse)
def sync_finance_statements(
    request: FinanceStatementsSyncRequest,
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return FinanceStatementService(settings, client, session).sync(request)


@router.post("/webhooks/company-details/sync", response_model=SyncResponse)
def sync_company_details(
    request: CompanyDetailsSyncRequest,
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return CompanyService(settings, client, session).sync(request)


@router.post("/webhooks/symbols/sync", response_model=SyncResponse)
def sync_symbols(
    request: SymbolsSyncRequest = Body(default_factory=SymbolsSyncRequest),
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return SymbolService(settings, client, session).sync(request)


@router.post("/webhooks/market-mentions/sync", response_model=SyncResponse)
def sync_market_mentions(
    request: MarketMentionsSyncRequest,
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return MarketService(settings, client, session).sync_mentions(request)


@router.post("/webhooks/session-quotes/sync", response_model=SyncResponse)
def sync_session_quotes(
    request: SessionQuotesSyncRequest,
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return MarketService(settings, client, session).sync_session_quotes(request)


@router.post("/webhooks/history-prices/sync", response_model=SyncResponse)
def sync_history_prices(
    request: HistoryPricesSyncRequest,
    settings: Settings = Depends(get_settings),
    client: ApiClient = Depends(get_client),
    session: Session = Depends(get_session),
) -> SyncResponse:
    return MarketService(settings, client, session).sync_history_prices(request)
