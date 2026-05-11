from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from common.orm.models import SyncDeadLetter, SyncOutbox
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.orm import Session

ENTITY_TYPES = {
    "symbol",
    "post",
    "tagged_symbol",
    "major_holder",
    "subsidiary",
    "report",
    "report_data",
    "market_mention",
    "chunk",
}
EVENT_ACTIONS = {"created", "updated", "deleted", "reindex", "graph_sync", "vector_sync"}
EVENT_STATUSES = {"pending", "processing", "processed", "failed"}


@dataclass(frozen=True)
class OutboxEvent:
    id: int
    entity_type: str
    entity_id: str
    action: str
    payload: dict[str, Any] | None
    status: str
    retry_count: int
    max_retries: int
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None
    locked_at: datetime | None
    lock_owner: str | None
    next_retry_at: datetime | None


class SyncOutboxService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue_event(
        self,
        entity_type: str,
        entity_id: str | int,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> int:
        self._validate(entity_type, action)
        row = SyncOutbox(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            payload=payload,
            status="pending",
            retry_count=0,
            max_retries=5,
            next_retry_at=None,
        )
        self.session.add(row)
        self.session.flush()
        logger.info(
            "Outbox event enqueued id={id} entity_type={entity_type} entity_id={entity_id} action={action}",
            id=row.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
        )
        return int(row.id)

    def enqueue_many(self, events: list[dict[str, Any]]) -> list[int]:
        ids: list[int] = []
        for event in events:
            ids.append(
                self.enqueue_event(
                    entity_type=str(event["entity_type"]),
                    entity_id=event["entity_id"],
                    action=str(event["action"]),
                    payload=event.get("payload"),
                )
            )
        return ids

    def fetch_pending(
        self,
        limit: int,
        worker_id: str,
        *,
        entity_types: set[str] | None = None,
        actions: set[str] | None = None,
    ) -> list[OutboxEvent]:
        now = datetime.now(UTC)
        retry_clause = (
            (SyncOutbox.status == "failed")
            & (SyncOutbox.retry_count < SyncOutbox.max_retries)
            & (SyncOutbox.next_retry_at.is_not(None))
            & (SyncOutbox.next_retry_at <= now)
        )
        stmt = select(SyncOutbox).where((SyncOutbox.status == "pending") | retry_clause)
        if entity_types:
            stmt = stmt.where(SyncOutbox.entity_type.in_(entity_types))
        if actions:
            stmt = stmt.where(SyncOutbox.action.in_(actions))
        stmt = stmt.order_by(SyncOutbox.created_at.asc()).limit(limit).with_for_update(skip_locked=True)
        rows = self.session.execute(stmt).scalars().all()
        events: list[OutboxEvent] = []
        for row in rows:
            row.status = "processing"
            row.locked_at = now
            row.lock_owner = worker_id
            row.error_message = None
            row.next_retry_at = None
            events.append(self._to_event(row))
        self.session.flush()
        return events

    def mark_processing(self, event_id: int, worker_id: str) -> None:
        self.session.execute(
            update(SyncOutbox)
            .where(SyncOutbox.id == event_id)
            .values(
                status="processing",
                lock_owner=worker_id,
                locked_at=datetime.now(UTC),
            )
        )

    def mark_processed(self, event_id: int) -> None:
        self.session.execute(
            update(SyncOutbox)
            .where(SyncOutbox.id == event_id)
            .values(
                status="processed",
                processed_at=datetime.now(UTC),
                lock_owner=None,
                locked_at=None,
                error_message=None,
                next_retry_at=None,
            )
        )

    def mark_failed(self, event_id: int, error_message: str) -> None:
        row = self.session.execute(
            select(SyncOutbox).where(SyncOutbox.id == event_id).limit(1)
        ).scalar_one_or_none()
        if row is None:
            return
        next_retry_count = row.retry_count + 1
        final_failed = next_retry_count >= row.max_retries
        backoff_seconds = min(300, 2 ** min(next_retry_count, 8))
        next_retry_at = None if final_failed else datetime.now(UTC) + timedelta(seconds=backoff_seconds)
        self.session.execute(
            update(SyncOutbox)
            .where(SyncOutbox.id == event_id)
            .values(
                status="failed" if final_failed else "pending",
                retry_count=next_retry_count,
                error_message=error_message[:4000],
                lock_owner=None,
                locked_at=None,
                next_retry_at=next_retry_at,
            )
        )
        if final_failed:
            self._push_dead_letter(
                source="outbox",
                event_id=event_id,
                error_message=error_message[:4000],
            )

    def enqueue_reindex_pair(
        self,
        entity_type: str,
        entity_id: str | int,
        payload: dict[str, Any] | None = None,
    ) -> list[int]:
        return self.enqueue_many(
            [
                {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "action": "graph_sync",
                    "payload": payload or {},
                },
                {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "action": "vector_sync",
                    "payload": payload or {},
                },
            ]
        )

    def push_worker_dead_letter(
        self,
        worker_name: str,
        error_message: str,
        payload: dict[str, Any] | None = None,
    ) -> int:
        row = SyncDeadLetter(
            source="worker_task",
            event_id=None,
            entity_type=(payload or {}).get("entity_type"),
            entity_id=str((payload or {}).get("entity_id")) if (payload or {}).get("entity_id") is not None else None,
            action=(payload or {}).get("action"),
            worker_name=worker_name,
            error_message=error_message[:4000],
            payload=payload,
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
        self.session.flush()
        return int(row.id)

    @staticmethod
    def _to_event(row: SyncOutbox) -> OutboxEvent:
        return OutboxEvent(
            id=int(row.id),
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            action=row.action,
            payload=row.payload,
            status=row.status,
            retry_count=row.retry_count,
            max_retries=row.max_retries,
            error_message=row.error_message,
            created_at=row.created_at,
            processed_at=row.processed_at,
            locked_at=row.locked_at,
            lock_owner=row.lock_owner,
            next_retry_at=row.next_retry_at,
        )

    @staticmethod
    def _validate(entity_type: str, action: str) -> None:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported entity_type '{entity_type}'")
        if action not in EVENT_ACTIONS:
            raise ValueError(f"Unsupported action '{action}'")

    def _push_dead_letter(self, source: str, event_id: int, error_message: str) -> None:
        event = self.session.execute(
            select(SyncOutbox).where(SyncOutbox.id == event_id).limit(1)
        ).scalar_one_or_none()
        row = SyncDeadLetter(
            source=source,
            event_id=event_id,
            entity_type=event.entity_type if event else None,
            entity_id=event.entity_id if event else None,
            action=event.action if event else None,
            worker_name=event.lock_owner if event else None,
            error_message=error_message[:4000],
            payload=event.payload if event else None,
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
