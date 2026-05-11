from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from common.orm.db.core import get_engine


@dataclass(frozen=True)
class TableChunkConfig:
    table: str
    key_columns: tuple[str, ...]
    chunk_columns: tuple[str, ...]
    order_columns: tuple[str, ...]


TABLES: dict[str, TableChunkConfig] = {
    "symbols": TableChunkConfig(
        table="symbols",
        key_columns=("ticker",),
        chunk_columns=("ticker", "company_name", "exchange", "sector", "industry", "short_industry"),
        order_columns=("ticker",),
    ),
    "history_prices": TableChunkConfig(
        table="history_prices",
        key_columns=("symbol_ticker", "date"),
        chunk_columns=("symbol_ticker", "date", "price_open", "price_close", "price_high", "price_low", "total_volume"),
        order_columns=("symbol_ticker", "date", "id"),
    ),
    "market_mentions": TableChunkConfig(
        table="market_mentions",
        key_columns=("symbol_ticker", "date"),
        chunk_columns=("symbol_ticker", "date", "day", "week", "month", "day_color", "week_color", "month_color"),
        order_columns=("symbol_ticker", "date", "id"),
    ),
    "session_quotes": TableChunkConfig(
        table="session_quotes",
        key_columns=("symbol_ticker", "datetime"),
        chunk_columns=("symbol_ticker", "datetime", "side", "match_price", "volume", "total_volume"),
        order_columns=("symbol_ticker", "datetime", "id"),
    ),
    "major_holders": TableChunkConfig(
        table="major_holders",
        key_columns=("symbol_ticker", "name"),
        chunk_columns=("symbol_ticker", "name", "position", "shares", "ownership", "reported"),
        order_columns=("symbol_ticker", "name", "id"),
    ),
    "subsidiaries": TableChunkConfig(
        table="subsidiaries",
        key_columns=("symbol_ticker", "sub_symbol"),
        chunk_columns=("symbol_ticker", "sub_symbol", "company_name", "type", "ownership", "shares"),
        order_columns=("symbol_ticker", "sub_symbol", "id"),
    ),
    "reports": TableChunkConfig(
        table="reports",
        key_columns=("id",),
        chunk_columns=("id", "symbol_ticker", "name", "display_name", "type", "lever"),
        order_columns=("id",),
    ),
    "report_data": TableChunkConfig(
        table="report_data",
        key_columns=("report_id", "year", "quarter"),
        chunk_columns=("report_id", "year", "quarter", "value"),
        order_columns=("report_id", "year", "quarter", "id"),
    ),
}


def _build_where_clause(filters: dict[str, Any], allowed_columns: tuple[str, ...]) -> tuple[str, dict[str, Any]]:
    if not filters:
        return "", {}

    clauses: list[str] = []
    params: dict[str, Any] = {}
    allowed = set(allowed_columns)
    for key, value in filters.items():
        if key not in allowed:
            raise ValueError(f"Column '{key}' is not allowed for this table")
        param_key = f"f_{key}"
        clauses.append(f"{key} = :{param_key}")
        params[param_key] = value
    return " WHERE " + " AND ".join(clauses), params


def _row_to_chunk(table: str, row: dict[str, Any], chunk_columns: tuple[str, ...]) -> str:
    parts = [f"table={table}"]
    for col in chunk_columns:
        value = row.get(col)
        if value is None or value == "":
            continue
        parts.append(f"{col}={value}")
    return " | ".join(parts)


def _encode_cursor(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str) -> dict[str, Any]:
    raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def _build_keyset_clause(order_columns: tuple[str, ...], cursor_values: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not cursor_values:
        return "", {}
    missing = [c for c in order_columns if c not in cursor_values]
    if missing:
        raise ValueError(f"Cursor missing fields: {', '.join(missing)}")

    # Lexicographic keyset:
    # (a,b,c) > (x,y,z) as:
    # a > x OR (a = x AND b > y) OR (a = x AND b = y AND c > z)
    parts: list[str] = []
    params: dict[str, Any] = {}
    for i, col in enumerate(order_columns):
        eq_prefix = " AND ".join([f"{order_columns[j]} = :k_eq_{j}" for j in range(i)])
        gt_expr = f"{col} > :k_gt_{i}"
        if eq_prefix:
            parts.append(f"({eq_prefix} AND {gt_expr})")
        else:
            parts.append(f"({gt_expr})")
        params[f"k_gt_{i}"] = cursor_values[col]
        for j in range(i):
            params[f"k_eq_{j}"] = cursor_values[order_columns[j]]
    return " AND (" + " OR ".join(parts) + ")", params


def check_chunks(
    table: str,
    filters: dict[str, Any],
    limit: int,
    keyword: str | None = None,
    cursor: str | None = None,
) -> tuple[int, list[str], str | None]:
    cfg = TABLES.get(table)
    if cfg is None:
        raise ValueError(f"Unsupported table '{table}'")

    where_clause, params = _build_where_clause(filters, cfg.key_columns + cfg.chunk_columns)
    cursor_values = _decode_cursor(cursor) if cursor else {}
    keyset_clause, keyset_params = _build_keyset_clause(cfg.order_columns, cursor_values)
    params.update(keyset_params)
    selected_cols = list(dict.fromkeys((*cfg.chunk_columns, *cfg.order_columns)))
    sql = text(
        f"SELECT {', '.join(selected_cols)} "
        f"FROM {cfg.table}{where_clause}{keyset_clause} "
        f"ORDER BY {', '.join(cfg.order_columns)} LIMIT :limit"
    )
    params["limit"] = limit + 1

    engine = get_engine()
    with engine.connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(sql, params).fetchall()]

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    chunks = [_row_to_chunk(cfg.table, row, cfg.chunk_columns) for row in page_rows]
    if keyword:
        k = keyword.lower().strip()
        chunks = [c for c in chunks if k in c.lower()]

    next_cursor: str | None = None
    if has_more and page_rows:
        last = page_rows[-1]
        next_cursor = _encode_cursor({col: last[col] for col in cfg.order_columns})
    return len(chunks), chunks, next_cursor
