from __future__ import annotations

from datetime import date, datetime


def parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
