from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

PRICE_COLUMNS = (
    "price_open",
    "price_high",
    "price_low",
    "price_average",
    "price_close",
    "price_basic",
)


def build_adjusted_history_frame(
    rows: Iterable[dict[str, Any]] | pd.DataFrame,
    *,
    price_columns: tuple[str, ...] = PRICE_COLUMNS,
) -> pd.DataFrame:
    """Return a DataFrame with raw and adjusted prices derived from adj_ratio.

    Raw prices remain the source of truth. Adjusted columns are computed as:
    adjusted_price = raw_price / adj_ratio
    for rows where adj_ratio is a positive number.
    """

    df = rows.copy() if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    if df.empty:
        return df

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(["symbol_ticker", "date"], kind="stable").reset_index(drop=True)

    if "adj_ratio" not in df.columns:
        raise KeyError("Expected column 'adj_ratio' to build adjusted price series")

    ratio = pd.to_numeric(df["adj_ratio"], errors="coerce")
    valid_ratio = ratio.where(ratio > 0)

    for column in price_columns:
        if column not in df.columns:
            continue
        prices = pd.to_numeric(df[column], errors="coerce")
        adjusted_column = f"adj_{column}"
        df[adjusted_column] = prices.where(valid_ratio.isna(), prices / valid_ratio)

    return df
