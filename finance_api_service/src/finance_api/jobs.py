from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from celery.result import AsyncResult

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


@dataclass
class JobRecord:
    job_id: str
    job_name: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    result: SyncResponse | None = None
    meta: dict[str, str] = field(default_factory=dict)


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def register(self, job_id: str, job_name: str, *, meta: dict[str, str] | None = None) -> JobRecord:
        record = JobRecord(
            job_id=job_id,
            job_name=job_name,
            status="queued",
            created_at=datetime.now(UTC),
            meta=meta or {},
        )
        with self._lock:
            self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)


job_registry = JobRegistry()


def _celery_app():
    from finance_api.celery_app import celery_app

    return celery_app


def _task_name(job_name: str) -> str:
    return f"finance_api.{job_name.removesuffix('_sync')}"


def enqueue_job(
    job_name: str,
    payload: dict[str, Any] | None = None,
    *,
    meta: dict[str, str] | None = None,
) -> JobRecord:
    task_name = _task_name(job_name)
    async_result = _celery_app().send_task(task_name, kwargs={"payload": payload or {}})
    return job_registry.register(async_result.id, job_name, meta=meta)


def get_job(job_id: str) -> JobRecord | None:
    record = job_registry.get(job_id)
    async_result = AsyncResult(job_id, app=_celery_app())
    if record is None:
        if async_result.state == "PENDING":
            return None
        record = JobRecord(
            job_id=job_id,
            job_name="unknown",
            status="queued",
            created_at=datetime.now(UTC),
        )

    state = async_result.state
    status = "queued"
    started_at = record.started_at
    finished_at = record.finished_at
    error = record.error
    result_payload = record.result

    if state == "STARTED":
        status = "running"
        started_at = started_at or datetime.now(UTC)
    elif state == "SUCCESS":
        raw_result = async_result.result or {}
        result_payload = SyncResponse(**raw_result) if isinstance(raw_result, dict) else None
        status = "completed" if result_payload is None or result_payload.status == "ok" else "partial_error"
        started_at = started_at or record.created_at
        finished_at = finished_at or datetime.now(UTC)
    elif state == "FAILURE":
        status = "failed"
        started_at = started_at or record.created_at
        finished_at = finished_at or datetime.now(UTC)
        error = str(async_result.result)
    elif state == "PENDING":
        status = "queued"
    else:
        status = "running"
        started_at = started_at or datetime.now(UTC)

    return JobRecord(
        job_id=record.job_id,
        job_name=record.job_name,
        status=status,
        created_at=record.created_at,
        started_at=started_at,
        finished_at=finished_at,
        error=error,
        result=result_payload,
        meta=record.meta,
    )


def enqueue_bootstrap_jobs(settings: Settings) -> list[JobRecord]:
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
    jobs: list[JobRecord] = []
    for job_name, payload in bootstrap_specs:
        job = enqueue_job(job_name, payload, meta={"bootstrap": "true"})
        logger.info("Bootstrap job queued job_name={job_name} job_id={job_id}", job_name=job_name, job_id=job.job_id)
        jobs.append(job)

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
