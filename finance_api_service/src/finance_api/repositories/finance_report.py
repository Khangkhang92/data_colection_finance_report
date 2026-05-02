from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finance_schema.models import Data, Report

DISPLAY_NAME: dict[str, str] = {}


class FinanceStatementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_period(self, symbol: str, report_type: int) -> tuple[int, int] | None:
        row = self.session.execute(
            select(Data.year, Data.quarter)
            .join(Report, Report.id == Data.report_id)
            .where(Report.symbol_ticker == symbol, Report.type == report_type)
            .order_by(Data.year.desc(), Data.quarter.desc())
            .limit(1)
        ).first()
        if row is None:
            return None
        return (row.year, row.quarter)

    def get_existing_periods(
        self,
        symbol: str,
        report_type: int,
        periods: Iterable[tuple[int, int]],
    ) -> set[tuple[int, int]]:
        target = set(periods)
        if not target:
            return set()

        rows = self.session.execute(
            select(Data.year, Data.quarter)
            .join(Report, Report.id == Data.report_id)
            .where(Report.symbol_ticker == symbol, Report.type == report_type)
            .distinct()
        ).all()
        return {(row.year, row.quarter) for row in rows if (row.year, row.quarter) in target}

    def has_missing_parent_links(self, symbol: str, report_type: int) -> bool:
        row = self.session.execute(
            select(Report.id)
            .where(
                Report.symbol_ticker == symbol,
                Report.type == report_type,
                Report.lever > 1,
                Report.parent_id.is_(None),
            )
            .limit(1)
        ).first()
        return row is not None

    def save_report_tree(self, data: list[dict], symbol: str, report_type: int) -> int:
        items = self._flatten_items(data)
        items.sort(key=self._item_sort_key)

        saved = 0
        report_ids_by_source_id: dict[int, int] = {}
        for item in items:
            parent_id = self._resolve_parent_id(item, report_ids_by_source_id)
            report_id = self._upsert_report(symbol, report_type, item, parent_id)
            source_id = item.get("id")
            if isinstance(source_id, int):
                report_ids_by_source_id[source_id] = report_id
            saved += self._upsert_values(report_id, item.get("values") or [])
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

    def _flatten_items(self, data: list[dict]) -> list[dict]:
        items: list[dict] = []
        stack = list(data)
        while stack:
            item = stack.pop(0)
            if not isinstance(item, dict):
                continue
            items.append(item)
            children = item.get("children")
            if isinstance(children, list):
                stack.extend(child for child in children if isinstance(child, dict))
        return items

    def _resolve_parent_id(
        self,
        item: dict,
        report_ids_by_source_id: dict[int, int],
    ) -> int | None:
        parent_source_id = item.get("parentID")
        if not isinstance(parent_source_id, int) or parent_source_id < 0:
            return None
        return report_ids_by_source_id.get(parent_source_id)

    def _item_sort_key(self, item: dict) -> tuple[int, int, str]:
        level = item.get("level")
        source_id = item.get("id")
        name = item.get("name")
        return (
            level if isinstance(level, int) else 0,
            source_id if isinstance(source_id, int) else 0,
            str(name or ""),
        )
