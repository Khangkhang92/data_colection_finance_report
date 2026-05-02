from __future__ import annotations

from pydantic import BaseModel


class JobAcceptedResponse(BaseModel):
    job_name: str
    accepted: bool = True
    message: str
