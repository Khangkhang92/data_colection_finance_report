from __future__ import annotations

import sys
from pathlib import Path

from celery import Celery
from celery.schedules import crontab

_HERE = Path(__file__).resolve()
_SERVICE_ROOT = _HERE.parents[2]
_BUSINESS_LOGIC_ROOT = _SERVICE_ROOT / "business_logic"
_COMMON_SERVICE_ROOT = _SERVICE_ROOT.parent / "common"
for path in (str(_SERVICE_ROOT), str(_BUSINESS_LOGIC_ROOT), str(_COMMON_SERVICE_ROOT)):
    if path not in sys.path:
        sys.path.append(path)

from common.config.finance_api import get_settings
from common.orm.db import session_scope
from services.finance_report.worker.jobs.sync_jobs import (
    process_sync_outbox_job,
    sync_company_details_job,
    sync_finance_statements_job,
    sync_graph_job,
    sync_history_prices_job,
    sync_market_mentions_job,
    sync_session_quotes_job,
    sync_symbols_job,
)
from business_logic.services.sync_outbox import SyncOutboxService

settings = get_settings()

celery_app = Celery(
    "finance_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    timezone=settings.celery_timezone,
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "sync-symbols-quarterly": {
            "task": "finance_api.sync_symbols",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=2, hour=6, minute=0),
        },
        "sync-company-details-quarterly": {
            "task": "finance_api.sync_company_details",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=3, hour=6, minute=30),
        },
        "sync-market-mentions-daily": {
            "task": "finance_api.sync_market_mentions",
            "schedule": crontab(hour=21, minute=0),
        },
        "sync-session-quotes-daily": {
            "task": "finance_api.sync_session_quotes",
            "schedule": crontab(hour=21, minute=15),
        },
        "sync-history-prices-daily": {
            "task": "finance_api.sync_history_prices",
            "schedule": crontab(hour=17, minute=0),
        },
        "sync-finance-statements-quarterly": {
            "task": "finance_api.sync_finance_statements",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=15, hour=19, minute=0),
        },
        "process-sync-outbox-every-minute": {
            "task": "finance_api.process_sync_outbox",
            "schedule": crontab(minute="*"),
        },
    },
)


@celery_app.task(name="finance_api.sync_symbols")
def sync_symbols_task() -> dict:
    return sync_symbols_job()


@celery_app.task(name="finance_api.sync_company_details")
def sync_company_details_task() -> dict:
    return sync_company_details_job()


@celery_app.task(name="finance_api.sync_market_mentions")
def sync_market_mentions_task() -> dict:
    return sync_market_mentions_job()


@celery_app.task(name="finance_api.sync_session_quotes")
def sync_session_quotes_task() -> dict:
    return sync_session_quotes_job()


@celery_app.task(name="finance_api.sync_history_prices")
def sync_history_prices_task() -> dict:
    return sync_history_prices_job()


@celery_app.task(name="finance_api.sync_finance_statements")
def sync_finance_statements_task() -> dict:
    return sync_finance_statements_job()


@celery_app.task(name="finance_api.sync_graph")
def sync_graph_task() -> dict:
    return sync_graph_job()


@celery_app.task(name="finance_api.process_sync_outbox")
def process_sync_outbox_task(limit: int = 100) -> dict:
    try:
        return process_sync_outbox_job(limit=limit)
    except Exception as exc:
        with session_scope() as session:
            SyncOutboxService(session).push_worker_dead_letter(
                worker_name="finance_api.process_sync_outbox",
                error_message=str(exc),
                payload={"limit": limit},
            )
        raise
