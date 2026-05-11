from __future__ import annotations

from time import perf_counter

from common.config.finance_rag import get_settings as get_finance_rag_settings
from common.orm.db import session_scope
from loguru import logger
from rag.vector_store import VectorSyncService
from services.finance_report.business_logic.services.sync_outbox import SyncOutboxService


def process_vector_outbox_job(limit: int = 100) -> dict:
    worker_id = "finance-rag-worker"
    started = perf_counter()
    stats = {"fetched": 0, "processed": 0, "failed": 0}

    with session_scope() as session:
        outbox = SyncOutboxService(session)
        events = outbox.fetch_pending(
            limit=limit,
            worker_id=worker_id,
            entity_types={"chunk", "post", "symbol", "report", "report_data", "market_mention"},
            actions={"created", "updated", "deleted", "vector_sync"},
        )
        stats["fetched"] = len(events)
        if not events:
            return {"status": "ok", "message": "no pending events", **stats}

        rag_settings = get_finance_rag_settings()
        vector = VectorSyncService(settings=rag_settings, session=session)

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
                v = vector.sync_vector_event(event_dict)
                logger.info(
                    "Outbox vector event processed id={id} entity_type={entity_type} entity_id={entity_id} action={action} vector={vector}",
                    id=event.id,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    action=event.action,
                    vector=v,
                )
                outbox.mark_processed(event.id)
                stats["processed"] += 1
                ok = True
            except Exception as exc:
                stats["failed"] += 1
                outbox.mark_failed(event.id, str(exc))
                logger.exception(
                    "Outbox vector event failed id={id} entity_type={entity_type} entity_id={entity_id} action={action}",
                    id=event.id,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    action=event.action,
                )
            finally:
                duration_ms = (perf_counter() - t0) * 1000
                logger.info(
                    "Outbox vector event done id={id} status={status} duration_ms={duration_ms:.2f}",
                    id=event.id,
                    status="processed" if ok else "failed",
                    duration_ms=duration_ms,
                )

    total_ms = (perf_counter() - started) * 1000
    return {"status": "ok", "duration_ms": round(total_ms, 2), **stats}
