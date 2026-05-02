from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finance_api.clients import ApiClient
from finance_api.config import Settings, get_settings
from finance_api.db import session_scope
from finance_api.schemas import (
    CompanyDetailsSyncRequest,
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
from loguru import logger


def _celery_app():
    from finance_api.celery_app import celery_app

    return celery_app


def _task_name(job_name: str) -> str:
    return f"finance_api.{job_name.removesuffix('_sync')}"


def enqueue_job(
    job_name: str,
    payload: dict[str, Any] | None = None,
) -> None:
    task_name = _task_name(job_name)
    _celery_app().send_task(task_name, kwargs={"payload": payload or {}})


def enqueue_bootstrap_jobs(settings: Settings) -> list[str]:
    marker_path: Path = settings.bootstrap_run_once_marker_path
    if not settings.bootstrap_run_all_jobs_on_startup:
        logger.info("Bootstrap sync disabled bootstrap_run_all_jobs_on_startup=false")
        return []
    if marker_path.exists():
        logger.info("Bootstrap sync skipped marker_exists path={path}", path=marker_path)
        return []

    logger.info("Bootstrap sync started path={path}", path=marker_path)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_specs: list[tuple[str, dict[str, Any]]] = [
        ("posts_sync", PostsSyncRequest().model_dump(mode="json")),
        ("symbols_sync", SymbolsSyncRequest().model_dump(mode="json")),
        ("finance_statements_sync", {}),
        ("company_details_sync", CompanyDetailsSyncRequest().model_dump(mode="json")),
        ("market_mentions_sync", MarketMentionsSyncRequest().model_dump(mode="json")),
        ("session_quotes_sync", SessionQuotesSyncRequest().model_dump(mode="json")),
        ("history_prices_sync", HistoryPricesSyncRequest().model_dump(mode="json")),
    ]
    jobs: list[str] = []
    for job_name, payload in bootstrap_specs:
        enqueue_job(job_name, payload)
        logger.info("Bootstrap job queued job_name={job_name}", job_name=job_name)
        jobs.append(job_name)

    marker_path.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")
    logger.info("Bootstrap sync finished queued_jobs={count} path={path}", count=len(jobs), path=marker_path)
    return jobs


def run_posts_sync(request: PostsSyncRequest) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return PostsService(settings, client, session).sync(request)


def run_finance_statements_sync() -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return FinanceStatementService(settings, client, session).sync()


def run_company_details_sync(request: CompanyDetailsSyncRequest) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return CompanyService(settings, client, session).sync(request)


def run_symbols_sync(request: SymbolsSyncRequest) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return SymbolService(settings, client, session).sync(request)


def run_market_mentions_sync(request: MarketMentionsSyncRequest | None = None) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return MarketService(settings, client, session).sync_mentions(request)


def run_session_quotes_sync(request: SessionQuotesSyncRequest | None = None) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return MarketService(settings, client, session).sync_session_quotes(
            request or SessionQuotesSyncRequest()
        )


def run_history_prices_sync(request: HistoryPricesSyncRequest | None = None) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return MarketService(settings, client, session).sync_history_prices(request)
