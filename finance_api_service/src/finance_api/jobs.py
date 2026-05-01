from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock, Thread
from typing import Callable
from uuid import uuid4

from finance_api.clients import ApiClient
from finance_api.config import Settings, get_settings
from finance_api.db import session_scope
from finance_api.schemas import (
    CompanyDetailsSyncRequest,
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


class BackgroundJobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def enqueue(
        self,
        job_name: str,
        runner: Callable[[], SyncResponse],
        *,
        dedupe_key: str | None = None,
    ) -> tuple[JobRecord, bool]:
        with self._lock:
            for job in self._jobs.values():
                if (
                    dedupe_key
                    and job.meta.get("dedupe_key") == dedupe_key
                    and job.status in {"queued", "running"}
                ):
                    return job, True

            job = JobRecord(
                job_id=str(uuid4()),
                job_name=job_name,
                status="queued",
                created_at=datetime.now(UTC),
                meta={"dedupe_key": dedupe_key or job_name},
            )
            self._jobs[job.job_id] = job

        thread = Thread(
            target=self._run_job,
            args=(job.job_id, runner),
            name=f"finance-job-{job_name}",
            daemon=True,
        )
        thread.start()
        return job, False

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run_job(self, job_id: str, runner: Callable[[], SyncResponse]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            job.started_at = datetime.now(UTC)

        try:
            logger.info("Background job started job_id={job_id} job_name={job_name}", job_id=job.job_id, job_name=job.job_name)
            result = runner()
        except Exception as exc:
            logger.exception("Background job failed job_id={job_id} job_name={job_name}", job_id=job.job_id, job_name=job.job_name)
            with self._lock:
                job = self._jobs[job_id]
                job.status = "failed"
                job.error = str(exc)
                job.finished_at = datetime.now(UTC)
            return

        with self._lock:
            job = self._jobs[job_id]
            job.status = "completed" if result.status == "ok" else "partial_error"
            job.result = result
            job.finished_at = datetime.now(UTC)
        logger.info("Background job finished job_id={job_id} job_name={job_name} status={status}", job_id=job.job_id, job_name=job.job_name, status=job.status)


job_manager = BackgroundJobManager()


def enqueue_bootstrap_jobs(settings: Settings) -> list[JobRecord]:
    marker_path = settings.bootstrap_run_once_marker_path
    if not settings.bootstrap_run_all_jobs_on_startup:
        logger.info("Bootstrap sync disabled bootstrap_run_all_jobs_on_startup=false")
        return []
    if marker_path.exists():
        logger.info("Bootstrap sync skipped marker_exists path={path}", path=marker_path)
        return []

    logger.info("Bootstrap sync started path={path}", path=marker_path)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    jobs: list[JobRecord] = []
    bootstrap_specs: list[tuple[str, Callable[[], SyncResponse], str]] = [
        ("posts_sync", lambda: run_posts_sync(PostsSyncRequest()), "posts_sync"),
        ("symbols_sync", lambda: run_symbols_sync(SymbolsSyncRequest()), "symbols_sync"),
        ("finance_statements_sync", run_finance_statements_sync, "finance_statements_sync"),
        (
            "company_details_sync",
            lambda: run_company_details_sync(CompanyDetailsSyncRequest()),
            "company_details_sync",
        ),
        ("market_mentions_sync", run_market_mentions_sync, "market_mentions_sync"),
        (
            "session_quotes_sync",
            lambda: run_session_quotes_sync(SessionQuotesSyncRequest()),
            "session_quotes_sync",
        ),
        ("history_prices_sync", run_history_prices_sync, "history_prices_sync"),
    ]

    for job_name, runner, dedupe_key in bootstrap_specs:
        job, deduplicated = job_manager.enqueue(job_name, runner, dedupe_key=dedupe_key)
        logger.info(
            "Bootstrap job queued job_name={job_name} job_id={job_id} deduplicated={deduplicated}",
            job_name=job.job_name,
            job_id=job.job_id,
            deduplicated=deduplicated,
        )
        jobs.append(job)

    marker_path.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")
    logger.info("Bootstrap sync finished queued_jobs={count} path={path}", count=len(jobs), path=marker_path)
    return jobs


def run_posts_sync(request) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return PostsService(settings, client, session).sync(request)


def run_finance_statements_sync() -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return FinanceStatementService(settings, client, session).sync()


def run_company_details_sync(request) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return CompanyService(settings, client, session).sync(request)


def run_symbols_sync(request) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return SymbolService(settings, client, session).sync(request)


def run_market_mentions_sync(request=None) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return MarketService(settings, client, session).sync_mentions(request)


def run_session_quotes_sync(request) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return MarketService(settings, client, session).sync_session_quotes(request)


def run_history_prices_sync(request=None) -> SyncResponse:
    settings = get_settings()
    client = ApiClient(settings)
    with session_scope() as session:
        return MarketService(settings, client, session).sync_history_prices(request)
