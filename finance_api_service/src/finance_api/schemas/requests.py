from __future__ import annotations

from datetime import date
from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FinancialReportType(IntEnum):
    BALANCE_SHEET = 1
    INCOME_STATEMENT = 2
    CASH_FLOW_DIRECT = 3
    CASH_FLOW_INDIRECT = 4


class SyncResponse(BaseModel):
    service: str
    status: str = "ok"
    fetched: int = 0
    saved: int = 0
    errors: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class PostsSyncRequest(BaseModel):
    total: int = 100
    post_type: int = 1
    step: int = 50
    params: dict[str, Any] = Field(default_factory=dict)


class FinanceStatementsSyncRequest(BaseModel):
    report_types: list[FinancialReportType] = Field(
        default_factory=lambda: [
            FinancialReportType.BALANCE_SHEET,
            FinancialReportType.INCOME_STATEMENT,
            FinancialReportType.CASH_FLOW_DIRECT,
            FinancialReportType.CASH_FLOW_INDIRECT,
        ]
    )
    # FireAnt returns data backwards from the anchor period. Use a long default
    # so the first run backfills the available history for every company.
    limit: int = 120


class CompanyDetailsSyncRequest(BaseModel):
    include_holders: bool = True
    include_subsidiaries: bool = True


class SymbolsSyncRequest(BaseModel):
    instrument_types: list[str] | None = Field(default_factory=lambda: ["stock"])
    include_auth: bool = True

    @field_validator("instrument_types", mode="before")
    @classmethod
    def normalize_instrument_types(cls, value: Any) -> list[str] | None:
        if value is None:
            return ["stock"]
        if not isinstance(value, list):
            return ["stock"]

        normalized = [
            str(item).strip().lower()
            for item in value
            if item is not None and str(item).strip() and str(item).strip().lower() != "string"
        ]
        return normalized or ["stock"]


class MarketMentionsSyncRequest(BaseModel):
    periods: list[str] = Field(default_factory=lambda: ["today", "weekly", "monthly"])
    target_date: date | None = None
    limit: int = 3000

    @field_validator("periods", mode="before")
    @classmethod
    def normalize_periods(cls, value: Any) -> list[str]:
        allowed = {"today", "weekly", "monthly"}
        if value is None or not isinstance(value, list):
            return ["today", "weekly", "monthly"]

        normalized = [
            str(item).strip().lower()
            for item in value
            if item is not None and str(item).strip().lower() in allowed
        ]
        return normalized or ["today", "weekly", "monthly"]


class SessionQuotesSyncRequest(BaseModel):
    pass


class HistoryPricesSyncRequest(BaseModel):
    limit: int = 100
