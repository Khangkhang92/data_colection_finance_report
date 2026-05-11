from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from common.orm.schemas.requests import SyncResponse


class JobAcceptedResponse(BaseModel):
    job_id: str
    job_name: str
    status: str
    deduplicated: bool = False
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    job_name: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    result: SyncResponse | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
