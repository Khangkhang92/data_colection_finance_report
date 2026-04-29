from __future__ import annotations

from fastapi import Depends

from finance_api.clients import ApiClient
from finance_api.config import Settings, get_settings


def get_client(settings: Settings = Depends(get_settings)) -> ApiClient:
    return ApiClient(settings)
