from __future__ import annotations

from pathlib import Path
from time import perf_counter

from common.orm.schemas.requests import CompanyDetailsSyncRequest, SymbolsSyncRequest
from business_logic.jobs import (
    run_company_details_sync,
    run_finance_statements_sync,
    run_graph_sync,
    run_history_prices_sync,
    run_market_mentions_sync,
    run_session_quotes_sync,
    run_symbols_sync,
)
from business_logic.services.graph_sync import GraphSyncService
from business_logic.services.sync_outbox import SyncOutboxService
from common.clients.neo4j import connect_neo4j
from common.config.finance_api import get_settings as get_finance_api_settings
from common.orm.db import session_scope
from loguru import logger


def sync_symbols_job() -> dict:
    return run_symbols_sync(SymbolsSyncRequest()).model_dump(mode="json")


def sync_company_details_job() -> dict:
    request = CompanyDetailsSyncRequest(include_holders=True, include_subsidiaries=True)
    return run_company_details_sync(request).model_dump(mode="json")


def sync_market_mentions_job() -> dict:
    return run_market_mentions_sync().model_dump(mode="json")


def sync_session_quotes_job() -> dict:
    return run_session_quotes_sync(None).model_dump(mode="json")


def sync_history_prices_job() -> dict:
    return run_history_prices_sync().model_dump(mode="json")


def sync_finance_statements_job() -> dict:
    return run_finance_statements_sync().model_dump(mode="json")


def sync_graph_job() -> dict:
    return run_graph_sync().model_dump(mode="json")


def process_sync_outbox_job(limit: int = 100) -> dict:
    worker_id = "finance-report-worker"
    started = perf_counter()
    stats = {"fetched": 0, "processed": 0, "failed": 0}

    with session_scope() as session:
        outbox = SyncOutboxService(session)
        events = outbox.fetch_pending(
            limit=limit,
            worker_id=worker_id,
            entity_types={"symbol", "post", "tagged_symbol", "major_holder", "subsidiary", "report", "report_data", "market_mention"},
            actions={"created", "updated", "deleted", "graph_sync"},
        )
        stats["fetched"] = len(events)
        if not events:
            return {"status": "ok", "message": "no pending events", **stats}

        api_settings = get_finance_api_settings()
        neo4j = connect_neo4j(
            uri=api_settings.neo4j_uri,
            username=api_settings.neo4j_username,
            password=api_settings.neo4j_password,
            database=api_settings.neo4j_database,
        )
        graph = GraphSyncService(session=session, neo4j=neo4j, batch_size=500)

        try:
            for event in events:
                t0 = perf_counter()
                ok = False
                try:
                    event_dict = {
                        "id": event.id,
                        "entity_type": event.entity_type,
                        "entity_id": event.entity_id,
                        "action": event.action,
                        "payload": event.payload,
                    }
                    g = graph.sync_entity_event(event_dict)
                    logger.info(
                        "Outbox graph event processed id={id} entity_type={entity_type} entity_id={entity_id} action={action} graph={graph}",
                        id=event.id,
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                        action=event.action,
                        graph=g,
                    )
                    outbox.mark_processed(event.id)
                    stats["processed"] += 1
                    ok = True
                except Exception as exc:
                    stats["failed"] += 1
                    outbox.mark_failed(event.id, str(exc))
                    logger.exception(
                        "Outbox event failed id={id} entity_type={entity_type} entity_id={entity_id} action={action}",
                        id=event.id,
                        entity_type=event.entity_type,
                        entity_id=event.entity_id,
                        action=event.action,
                    )
                finally:
                    duration_ms = (perf_counter() - t0) * 1000
                    logger.info(
                        "Outbox event done id={id} status={status} duration_ms={duration_ms:.2f}",
                        id=event.id,
                        status="processed" if ok else "failed",
                        duration_ms=duration_ms,
                    )
        finally:
            neo4j.close()

    total_ms = (perf_counter() - started) * 1000
    return {"status": "ok", "duration_ms": round(total_ms, 2), **stats}
