from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finance_schema.models import Symbol


class SymbolRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_symbol(self, row: dict) -> None:
        stmt = insert(Symbol).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_={key: row.get(key) for key in row if key != "ticker"},
        )
        self.session.execute(stmt)
