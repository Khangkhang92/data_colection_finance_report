from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


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
    symbols: list[str] | None = None
    report_types: list[int] = Field(default_factory=lambda: [1, 2])
    year: int
    quarter: int
    limit: int = 1


class CompanyDetailsSyncRequest(BaseModel):
    symbols: list[str] | None = None
    include_holders: bool = True
    include_subsidiaries: bool = True


class SymbolsSyncRequest(BaseModel):
    instrument_types: list[str] | None = Field(default_factory=lambda: ["stock"])
    include_auth: bool = True


class MarketMentionsSyncRequest(BaseModel):
    periods: list[str] = Field(default_factory=lambda: ["today", "weekly", "monthly"])
    target_date: date | None = None
    limit: int = 3000


class SessionQuotesSyncRequest(BaseModel):
    symbols: list[str] | None = None


class HistoryPricesSyncRequest(BaseModel):
    symbols: list[str] | None = None
    start_date: date
    end_date: date
    limit: int = 100
