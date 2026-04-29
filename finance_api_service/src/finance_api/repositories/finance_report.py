from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finance_schema.models import Data, Report

DISPLAY_NAME: dict[str, str] = {}


class FinanceStatementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_report_tree(self, data: list[dict], symbol: str, report_type: int) -> int:
        return self._save_items(data, data, symbol, report_type, parent_id=None)

    def _save_items(
        self,
        all_items: list[dict],
        items: list[dict],
        symbol: str,
        report_type: int,
        parent_id: int | None,
    ) -> int:
        saved = 0
        for item in list(items):
            report_id = self._upsert_report(symbol, report_type, item, parent_id)
            saved += self._upsert_values(report_id, item.get("values") or [])
            children = self._extract_children(all_items, item)
            saved += self._save_items(all_items, children, symbol, report_type, report_id)
        return saved

    def _upsert_report(
        self,
        symbol: str,
        report_type: int,
        item: dict,
        parent_id: int | None,
    ) -> int:
        name = item.get("name")
        values = {
            "symbol_ticker": symbol,
            "type": report_type,
            "lever": item.get("level"),
            "parent_id": parent_id,
            "name": name,
            "display_name": DISPLAY_NAME.get(name, name),
        }
        stmt = insert(Report).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["name", "symbol_ticker"],
            set_={
                "type": report_type,
                "lever": item.get("level"),
                "parent_id": parent_id,
                "display_name": values["display_name"],
            },
        )
        self.session.execute(stmt)
        return self.session.execute(
            select(Report.id).where(Report.name == name, Report.symbol_ticker == symbol)
        ).scalar_one()

    def _upsert_values(self, report_id: int, values: list[dict]) -> int:
        saved = 0
        for value in values:
            if value.get("value") is None:
                continue
            row = {
                "report_id": report_id,
                "value": value.get("value"),
                "year": value.get("year"),
                "quarter": value.get("quarter"),
            }
            stmt = insert(Data).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["report_id", "quarter", "year"],
                set_={"value": row["value"]},
            )
            self.session.execute(stmt)
            saved += 1
        return saved

    def _extract_children(self, data: list[dict], item: dict) -> list[dict]:
        item_id = item.get("id")
        children: list[dict] = []
        rest: list[dict] = []
        for candidate in data:
            if candidate.get("parentID") == item_id:
                children.append(candidate)
            else:
                rest.append(candidate)
        data[:] = rest
        return children
