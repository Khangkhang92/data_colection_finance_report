from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from finance_api.config import get_settings
from finance_api.jobs import (
    run_company_details_sync,
    run_extended_instruments_sync,
    run_finance_statements_sync,
    run_fundamentals_sync,
    run_history_prices_sync,
    run_industries_sync,
    run_market_mentions_sync,
    run_posts_sync,
    run_session_quotes_sync,
    run_symbols_sync,
)
from finance_api.schemas.requests import (
    CompanyDetailsSyncRequest,
    ExtendedInstrumentsSyncRequest,
    FundamentalsSyncRequest,
    HistoryPricesSyncRequest,
    IndustriesSyncRequest,
    MarketMentionsSyncRequest,
    PostsSyncRequest,
    SessionQuotesSyncRequest,
    SymbolsSyncRequest,
)


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
    task_track_started=True,
    beat_schedule={
        # Dong bo danh muc symbol theo quy, o thang T+1 sau khi quy ket thuc.
        # Chay luc 06:00, ngay 02 cua cac thang 01, 04, 07, 10.
        "sync-symbols-quarterly": {
            "task": "finance_api.sync_symbols",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=2, hour=6, minute=0),
        },
        # Dong bo danh muc nganh FireAnt va mapping nganh cho symbol sau symbol sync.
        "sync-industries-quarterly": {
            "task": "finance_api.sync_industries",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=2, hour=6, minute=15),
        },
        # Sau khi cap nhat symbol, dong bo thong tin doanh nghiep theo quy.
        # Chay luc 06:30, ngay 03 cua cac thang 01, 04, 07, 10.
        "sync-company-details-quarterly": {
            "task": "finance_api.sync_company_details",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=3, hour=6, minute=30),
        },
        # Snapshot free-float, shares outstanding va market cap cho LCDT.
        # Chay truoc history/session quote de co du bien quy mo trong bang market.
        "sync-fundamentals-daily": {
            "task": "finance_api.sync_fundamentals",
            "schedule": crontab(hour=7, minute=30),
        },
        # Metadata futures, covered warrants, ETF details va MXV commodity contracts.
        "sync-extended-instruments-daily": {
            "task": "finance_api.sync_extended_instruments",
            "schedule": crontab(hour=7, minute=45),
        },
        # Market mentions la du lieu co tinh chat gan real-time hon,
        # nhung job nay hien duoc chot 1 lan vao buoi sang de lay snapshot.
        # 08:00 Asia/Ho_Chi_Minh.
        "sync-market-mentions-daily": {
            "task": "finance_api.sync_market_mentions",
            "schedule": crontab(hour=8, minute=0),
        },
        # Session quotes nen chay sau khi phien giao dich trong ngay da on dinh.
        # 16:15 Asia/Ho_Chi_Minh.
        "sync-session-quotes-daily": {
            "task": "finance_api.sync_session_quotes",
            "schedule": crontab(hour=16, minute=15),
        },
        # History prices duoc resume theo latest_date trong DB,
        # vi vay chot lich cuoi ngay la hop ly nhat.
        # 17:00 Asia/Ho_Chi_Minh.
        "sync-history-prices-daily": {
            "task": "finance_api.sync_history_prices",
            "schedule": crontab(hour=17, minute=0),
        },
        # Bao cao tai chinh khong nen chay hang ngay.
        # Lich nay chay theo quy, vao thang T+1 sau khi quy ket thuc:
        # - Q4 nam truoc  -> thang 01
        # - Q1 nam hien tai -> thang 04
        # - Q2 nam hien tai -> thang 07
        # - Q3 nam hien tai -> thang 10
        #
        # Chot vao ngay 15 luc 19:00 Asia/Ho_Chi_Minh de giam rui ro
        # keo qua som khi doanh nghiep va FireAnt chua cap nhat du.
        "sync-finance-statements-quarterly": {
            "task": "finance_api.sync_finance_statements",
            "schedule": crontab(month_of_year="1,4,7,10", day_of_month=15, hour=19, minute=0),
        },
    },
)


@celery_app.task(name="finance_api.posts")
def sync_posts_task(payload: dict | None = None) -> dict:
    request = PostsSyncRequest(**(payload or {}))
    return run_posts_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_symbols")
def sync_symbols_task(payload: dict | None = None) -> dict:
    request = SymbolsSyncRequest(**(payload or {}))
    return run_symbols_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_industries")
def sync_industries_task(payload: dict | None = None) -> dict:
    request = IndustriesSyncRequest(**(payload or {}))
    return run_industries_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_company_details")
def sync_company_details_task(payload: dict | None = None) -> dict:
    request = CompanyDetailsSyncRequest(**(payload or {}))
    return run_company_details_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_market_mentions")
def sync_market_mentions_task(payload: dict | None = None) -> dict:
    request = MarketMentionsSyncRequest(**(payload or {}))
    return run_market_mentions_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_fundamentals")
def sync_fundamentals_task(payload: dict | None = None) -> dict:
    request = FundamentalsSyncRequest(**(payload or {}))
    return run_fundamentals_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_extended_instruments")
def sync_extended_instruments_task(payload: dict | None = None) -> dict:
    request = ExtendedInstrumentsSyncRequest(**(payload or {}))
    return run_extended_instruments_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_session_quotes")
def sync_session_quotes_task(payload: dict | None = None) -> dict:
    request = SessionQuotesSyncRequest(**(payload or {}))
    return run_session_quotes_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_history_prices")
def sync_history_prices_task(payload: dict | None = None) -> dict:
    request = HistoryPricesSyncRequest(**(payload or {}))
    return run_history_prices_sync(request).model_dump(mode="json")


@celery_app.task(name="finance_api.sync_finance_statements")
def sync_finance_statements_task(payload: dict | None = None) -> dict:
    return run_finance_statements_sync().model_dump(mode="json")
