from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from common.orm.models import DetailNewPost, NewPostsContent


class DetailNewPostsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def fetch_targets(self, *, limit: int, menu_name: str | None, only_missing_detail: bool) -> list[tuple[int, int]]:
        stmt = select(NewPostsContent.id, NewPostsContent.fireant_post_id).order_by(NewPostsContent.id.desc())
        if menu_name:
            stmt = stmt.where(NewPostsContent.menu_name == menu_name)
        if only_missing_detail:
            subq = select(DetailNewPost.new_post_content_id)
            stmt = stmt.where(~NewPostsContent.id.in_(subq))
        stmt = stmt.limit(limit)
        rows = self.session.execute(stmt).all()
        return [(int(r[0]), int(r[1])) for r in rows]

    def upsert_detail(self, *, new_post_content_id: int, fireant_post_id: int, detail_row: dict) -> None:
        now = datetime.now(UTC)
        values = {
            "new_post_content_id": new_post_content_id,
            "fireant_post_id": fireant_post_id,
            "detail_content": detail_row.get("content") or detail_row.get("description"),
            "detail_original_content": detail_row.get("originalContent"),
            "detail_summary": detail_row.get("summary"),
            "detail_payload": detail_row,
            "updated_at": now,
        }
        stmt = insert(DetailNewPost).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["new_post_content_id"],
            set_=values,
        )
        self.session.execute(stmt)
