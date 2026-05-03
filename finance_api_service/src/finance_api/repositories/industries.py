from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finance_schema.models import Industry, Symbol


class IndustryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_industry(self, row: dict) -> None:
        stmt = insert(Industry).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["industry_code"],
            set_={key: row.get(key) for key in row if key != "industry_code"},
        )
        self.session.execute(stmt)

    def upsert_symbol_mapping(self, row: dict) -> None:
        ticker = row.get("ticker")
        if not ticker:
            return

        if row.get("exchange"):
            stmt = insert(Symbol).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["ticker"],
                set_={key: row.get(key) for key in row if key != "ticker"},
            )
            self.session.execute(stmt)
            return

        values = {
            key: value
            for key, value in row.items()
            if key != "ticker" and value is not None
        }
        if values:
            self.session.execute(
                update(Symbol)
                .where(Symbol.ticker == ticker)
                .values(**values)
            )
