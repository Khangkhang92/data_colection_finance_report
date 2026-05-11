from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from common.orm.models import Post, PostGroup, PostSource, Symbol, TaggedSymbol


class PostsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def existing_symbols(self) -> set[str]:
        return set(self.session.execute(select(Symbol.ticker)).scalars().all())

    def save_posts(self, rows: list[dict]) -> int:
        saved = 0
        symbols = self.existing_symbols()

        for row in rows:
            post_group_id = self._upsert_group(row.get("postGroup"))
            post_source_id = self._upsert_source(row.get("postSource"))

            post_values = Post.from_json(row)
            post_values["post_group_id"] = post_group_id
            post_values["post_source_id"] = post_source_id

            stmt = insert(Post).values(**post_values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["fireant_post_id"],
                set_=post_values,
            )
            self.session.execute(stmt)

            post_id = self.session.execute(
                select(Post.post_id).where(Post.fireant_post_id == post_values["fireant_post_id"])
            ).scalar_one()

            self.session.execute(delete(TaggedSymbol).where(TaggedSymbol.post_id == post_id))
            tagged = [
                TaggedSymbol(post_id=post_id, symbol_ticker=item["symbol"])
                for item in row.get("taggedSymbols", [])
                if item.get("symbol") in symbols
            ]
            self.session.add_all(tagged)
            saved += 1

        return saved

    def _upsert_group(self, group: dict | None) -> int | None:
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

    def _upsert_source(self, source: dict | None) -> int | None:
        if not source:
            return None
        values = PostSource.from_json(source)
        stmt = insert(PostSource).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["fireant_post_source_id"],
            set_=values,
        )
        self.session.execute(stmt)
        return self.session.execute(
            select(PostSource.post_source_id).where(
                PostSource.fireant_post_source_id == values["fireant_post_source_id"]
            )
        ).scalar_one()
