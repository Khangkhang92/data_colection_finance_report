from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock, Thread
from typing import Callable
from uuid import uuid4

from business_logic.clients import ApiClient
from business_logic.services.company import CompanyService
from business_logic.services.finance_report import FinanceStatementService
from business_logic.services.graph_sync import GraphSyncService
from business_logic.services.market import MarketService
from business_logic.services.posts import PostsService
from business_logic.services.symbols import SymbolService
from common.clients.neo4j import connect_neo4j
from common.config.finance_api import get_settings
from common.orm.db import session_scope
from common.orm.schemas import SyncResponse
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
            logger.info(
                "Background job started job_id={job_id} job_name={job_name}",
                job_id=job.job_id,
                job_name=job.job_name,
            )
            result = runner()
        except Exception as exc:
            logger.exception(
                "Background job failed job_id={job_id} job_name={job_name}",
                job_id=job.job_id,
                job_name=job.job_name,
            )
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
        logger.info(
            "Background job finished job_id={job_id} job_name={job_name} status={status}",
            job_id=job.job_id,
            job_name=job.job_name,
            status=job.status,
        )


job_manager = BackgroundJobManager()


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


def run_graph_sync() -> SyncResponse:
    settings = get_settings()
    errors: list[str] = []
    try:
        neo4j = connect_neo4j(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
    except Exception as exc:
        return SyncResponse(service="neo4j_graph", status="failed", errors=[f"connect neo4j failed: {exc}"])

    try:
        if not neo4j.health_check():
            return SyncResponse(service="neo4j_graph", status="failed", errors=["neo4j health check failed"])

        with session_scope() as session:
            stats = GraphSyncService(session=session, neo4j=neo4j, batch_size=500).sync_all()
        saved = sum(stats.to_dict().values())
        return SyncResponse(
            service="neo4j_graph",
            status="ok" if not errors else "partial_error",
            fetched=saved,
            saved=saved,
            errors=errors,
            meta=stats.to_dict(),
        )
    except Exception as exc:
        logger.exception("Neo4j graph sync failed")
        return SyncResponse(service="neo4j_graph", status="failed", errors=[str(exc)])
    finally:
        neo4j.close()
