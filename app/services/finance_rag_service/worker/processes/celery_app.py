from __future__ import annotations

import sys
from pathlib import Path

from celery import Celery
from celery.schedules import crontab

_HERE = Path(__file__).resolve()
_SERVICE_ROOT = _HERE.parents[2]
_BUSINESS_LOGIC_ROOT = _SERVICE_ROOT / "business_logic"
_COMMON_ROOT = _SERVICE_ROOT.parents[2] / "common"
for path in (str(_SERVICE_ROOT), str(_BUSINESS_LOGIC_ROOT), str(_COMMON_ROOT)):
    if path not in sys.path:
        sys.path.append(path)

from common.config.finance_rag import get_settings
from common.orm.db import session_scope
from services.finance_rag_service.worker.jobs.precompute_jobs import (
    conversation_summarization_worker,
    graph_context_precompute_worker,
    market_summary_precompute_worker,
    popular_query_precompute_worker,
    retrieval_cache_refresh_worker,
    sample_qa_precompute_worker,
    stale_cache_cleanup_worker,
    symbol_profile_precompute_worker,
)
from services.finance_report.business_logic.services.sync_outbox import SyncOutboxService
from services.finance_rag_service.worker.jobs.sync_jobs import process_vector_outbox_job

settings = get_settings()

broker_url = settings.redis_url
backend_url = settings.redis_url[:-1] + "1" if settings.redis_url.endswith("/0") else settings.redis_url

celery_app = Celery("finance_rag", broker=broker_url, backend=backend_url)
celery_app.conf.update(
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "process-vector-outbox-every-minute": {
            "task": "finance_rag.process_vector_outbox",
            "schedule": crontab(minute="*"),
        },
        "sample-qa-precompute-hourly": {
            "task": "finance_rag.sample_qa_precompute",
            "schedule": crontab(minute=10),
        },
        "popular-query-precompute-every-15m": {
            "task": "finance_rag.popular_query_precompute",
            "schedule": crontab(minute="*/15"),
        },
        "symbol-profile-precompute-hourly": {
            "task": "finance_rag.symbol_profile_precompute",
            "schedule": crontab(minute=20),
        },
        "market-summary-precompute-every-30m": {
            "task": "finance_rag.market_summary_precompute",
            "schedule": crontab(minute="*/30"),
        },
        "stale-cache-cleanup-hourly": {
            "task": "finance_rag.stale_cache_cleanup",
            "schedule": crontab(minute=45),
        },
        "retrieval-cache-refresh-every-20m": {
            "task": "finance_rag.retrieval_cache_refresh",
            "schedule": crontab(minute="*/20"),
        },
        "graph-context-precompute-every-20m": {
            "task": "finance_rag.graph_context_precompute",
            "schedule": crontab(minute="*/20"),
        },
        "conversation-summary-hourly": {
            "task": "finance_rag.conversation_summarization",
            "schedule": crontab(minute=55),
        },
    },
)


@celery_app.task(name="finance_rag.process_vector_outbox")
def process_vector_outbox_task(limit: int = 100) -> dict:
    return _run_with_dlq("finance_rag.process_vector_outbox", process_vector_outbox_job, limit=limit)


@celery_app.task(name="finance_rag.conversation_summarization")
def conversation_summarization_task(limit: int = 100) -> dict:
    return _run_with_dlq("finance_rag.conversation_summarization", conversation_summarization_worker, limit=limit)


@celery_app.task(name="finance_rag.popular_query_precompute")
def popular_query_precompute_task(limit: int = 50) -> dict:
    return _run_with_dlq("finance_rag.popular_query_precompute", popular_query_precompute_worker, limit=limit)


@celery_app.task(name="finance_rag.symbol_profile_precompute")
def symbol_profile_precompute_task(limit: int = 200) -> dict:
    return _run_with_dlq("finance_rag.symbol_profile_precompute", symbol_profile_precompute_worker, limit=limit)


@celery_app.task(name="finance_rag.market_summary_precompute")
def market_summary_precompute_task(limit: int = 100) -> dict:
    return _run_with_dlq("finance_rag.market_summary_precompute", market_summary_precompute_worker, limit=limit)


@celery_app.task(name="finance_rag.stale_cache_cleanup")
def stale_cache_cleanup_task(db_limit: int = 1000) -> dict:
    return _run_with_dlq("finance_rag.stale_cache_cleanup", stale_cache_cleanup_worker, db_limit=db_limit)


@celery_app.task(name="finance_rag.sample_qa_precompute")
def sample_qa_precompute_task(limit: int = 200) -> dict:
    return _run_with_dlq("finance_rag.sample_qa_precompute", sample_qa_precompute_worker, limit=limit)


@celery_app.task(name="finance_rag.retrieval_cache_refresh")
def retrieval_cache_refresh_task(limit: int = 100) -> dict:
    return _run_with_dlq("finance_rag.retrieval_cache_refresh", retrieval_cache_refresh_worker, limit=limit)


@celery_app.task(name="finance_rag.graph_context_precompute")
def graph_context_precompute_task(limit: int = 200) -> dict:
    return _run_with_dlq("finance_rag.graph_context_precompute", graph_context_precompute_worker, limit=limit)


def _run_with_dlq(worker_name: str, fn, **kwargs):  # type: ignore[no-untyped-def]
    try:
        return fn(**kwargs)
    except Exception as exc:
        with session_scope() as session:
            SyncOutboxService(session).push_worker_dead_letter(
                worker_name=worker_name,
                error_message=str(exc),
                payload={"kwargs": kwargs},
            )
        raise
