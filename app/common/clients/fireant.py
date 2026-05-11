from __future__ import annotations

import time
from typing import Any

import httpx
from loguru import logger

from common.config.finance_api import Settings


class ApiClientError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self, include_auth: bool = True) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Origin": "https://fireant.vn",
            "Referer": "https://fireant.vn/",
            "User-Agent": "finance-api-service/0.1.0",
        }
        if include_auth and self.settings.token_rest2:
            headers["Authorization"] = f"Bearer {self.settings.token_rest2}"
        return headers

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        include_auth: bool = True,
    ) -> Any:
        if not url:
            raise ApiClientError("Missing API URL")

        last_error: Exception | None = None
        attempts = max(self.settings.http_max_retries, 1)
        for attempt in range(attempts):
            try:
                logger.info(
                    "API GET started url={url} attempt={attempt}/{attempts}",
                    url=url,
                    attempt=attempt + 1,
                    attempts=attempts,
                )
                with httpx.Client(timeout=self.settings.http_timeout_seconds) as client:
                    response = client.get(url, params=params, headers=self._headers(include_auth))
                    response.raise_for_status()
                    logger.info(
                        "API GET finished url={url} status={status}",
                        url=url,
                        status=response.status_code,
                    )
                    return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                error_text = str(exc)
                logger.warning(
                    "API GET failed url={url} attempt={attempt}/{attempts} error={error}",
                    url=url,
                    attempt=attempt + 1,
                    attempts=attempts,
                    error=error_text,
                )
                if attempt < attempts - 1:
                    time.sleep(self.settings.http_retry_delay_seconds)

        logger.error(
            "API GET exhausted retries url={url} error={error}",
            url=url,
            error=str(last_error) if last_error else "unknown error",
        )
        raise ApiClientError(f"GET {url} failed: {last_error}")
