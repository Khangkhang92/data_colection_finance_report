from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from common.orm.models import RagChatMessage
from sqlalchemy import desc, select
from sqlalchemy.orm import Session


class ChatHistoryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append_message(
        self,
        conversation_id: str,
        user_id: str | None,
        role: str,
        content: str,
        *,
        sources: list[dict[str, Any]] | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> int:
        row = RagChatMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            sources=sources,
            metadata_json=metadata_json,
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
        self.session.flush()
        return int(row.id)

    def list_recent(self, conversation_id: str, limit: int = 50) -> list[RagChatMessage]:
        stmt = (
            select(RagChatMessage)
            .where(RagChatMessage.conversation_id == conversation_id)
            .order_by(desc(RagChatMessage.created_at))
            .limit(limit)
        )
        return list(reversed(self.session.execute(stmt).scalars().all()))
