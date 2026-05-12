from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from common.orm.models import NewPostsContent, NewPostsContentPostGroup, PostGroup


class NewPostsContentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_rows(self, menu_name: str, rows: list[dict]) -> int:
        saved = 0
        now = datetime.now(UTC)
        for row in rows:
            fireant_post_id = row.get("id") or row.get("postID")
            if fireant_post_id is None:
                continue

            values = {
                "menu_name": menu_name,
                "fireant_post_id": int(fireant_post_id),
                "user_id": self._extract_user_id(row),
                "user_name": row.get("userName"),
                "title": row.get("title"),
                "description": row.get("description"),
                "summary": row.get("summary"),
                "content": row.get("content") or row.get("description"),
                "original_content": row.get("originalContent"),
                "language": row.get("language"),
                "post_type": row.get("type"),
                "approved": row.get("approved"),
                "is_expert_idea": row.get("isExpertIdea"),
                "total_likes": row.get("totalLikes"),
                "total_replies": row.get("totalReplies"),
                "total_shares": row.get("totalShares"),
                "post_source_url": row.get("postSourceUrl"),
                "tagged_symbols": row.get("taggedSymbols"),
                "images": row.get("images"),
                "published_at": self._parse_dt(
                    row.get("date") or row.get("publishedAt") or row.get("createdAt")
                ),
                "author": self._extract_author(row),
                "source_url": row.get("contentURL") or row.get("url") or row.get("link"),
                "payload": row,
                "updated_at": now,
            }
            stmt = insert(NewPostsContent).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["menu_name", "fireant_post_id"],
                set_=values,
            )
            self.session.execute(stmt)
            new_post_id = self.session.execute(
                select(NewPostsContent.id).where(
                    NewPostsContent.menu_name == menu_name,
                    NewPostsContent.fireant_post_id == int(fireant_post_id),
                )
            ).scalar_one()
            self._replace_post_groups(new_post_id, row.get("postGroup"))
            saved += 1
        return saved

    def _replace_post_groups(self, new_post_id: int, post_group: dict | None) -> None:
        self.session.execute(
            delete(NewPostsContentPostGroup).where(
                NewPostsContentPostGroup.new_post_content_id == new_post_id
            )
        )
        if not post_group:
            return
        pg_id = self._upsert_post_group(post_group)
        if pg_id is None:
            return
        stmt = insert(NewPostsContentPostGroup).values(
            new_post_content_id=new_post_id,
            post_group_id=pg_id,
        )
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["new_post_content_id", "post_group_id"]
        )
        self.session.execute(stmt)

    def _upsert_post_group(self, group: dict | None) -> int | None:
        if not group:
            return None
        values = PostGroup.from_json(group)
        stmt = insert(PostGroup).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["fireant_post_group_id"],
            set_=values,
        )
        self.session.execute(stmt)
        return self.session.execute(
            select(PostGroup.post_group_id).where(
                PostGroup.fireant_post_group_id == values["fireant_post_group_id"]
            )
        ).scalar_one()

    @staticmethod
    def _extract_author(row: dict) -> str | None:
        author = row.get("author")
        if isinstance(author, dict):
            return author.get("name") or author.get("username")
        if isinstance(author, str):
            return author
        return row.get("authorName")

    @staticmethod
    def _extract_user_id(row: dict) -> str | None:
        user = row.get("user")
        if isinstance(user, dict):
            val = user.get("id")
            return str(val) if val is not None else None
        return None

    @staticmethod
    def _parse_dt(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            text = value.strip().replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(text)
            except ValueError:
                return None
        return None
