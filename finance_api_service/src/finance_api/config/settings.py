from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "fireant-data"
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    token_rest2: str | None = Field(default=None, alias="TOKEN_REST2")
    http_timeout_seconds: float = 30
    http_max_retries: int = 2
    http_retry_delay_seconds: float = 2
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_timezone: str = "Asia/Ho_Chi_Minh"
    bootstrap_run_all_jobs_on_startup: bool = False
    bootstrap_run_once_marker_path: Path = Path("/tmp/fireant-data-bootstrap.done")

    post_url: str | None = Field(default=None, alias="POST")
    post_source_url: str | None = Field(default=None, alias="POST_SOURCE")
    source_group_url: str | None = Field(default=None, alias="SOURCE_GROUP")
    holder_url: str | None = Field(default=None, alias="HOLDER")
    subsidiaries_url: str | None = Field(default=None, alias="SUBSIDIARIES")
    finance_url: str | None = Field(default=None, alias="FiNANCE_URL2")
    all_symbol_url: str | None = Field(default=None, alias="ALL_SYMBOL_URL2")
    market_mention_url: str | None = Field(default=None, alias="MARKET_MENTION")
    session_quote_url: str | None = Field(default=None, alias="BUY_SELL_DURING_SESSION")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
