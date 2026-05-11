from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


def upsert_one(
    session: Session,
    model: Any,
    values: dict[str, Any],
    conflict_columns: list[str],
    update_columns: list[str] | None = None,
) -> None:
    update_columns = update_columns or [key for key in values if key not in conflict_columns]
    stmt = insert(model).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_={column: values.get(column) for column in update_columns},
    )
    session.execute(stmt)


def insert_ignore(session: Session, model: Any, values: dict[str, Any], conflict_columns: list[str]) -> None:
    stmt = insert(model).values(**values)
    stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)
    session.execute(stmt)
