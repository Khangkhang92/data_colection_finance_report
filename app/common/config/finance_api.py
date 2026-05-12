from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[4]
_SERVICE_ROOT = _PROJECT_ROOT / "app" / "services" / "finance_report"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_PROJECT_ROOT / ".env"), str(_SERVICE_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "fireant-data"
    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    token_rest2: str | None = Field(default=None, alias="TOKEN_REST2")
    token: str | None = Field(default=None, alias="TOKEN")
    fire_ant_anoymous_token: str | None = Field(default=None, alias="FIRE_ANT_ANOYMOUS_TOKEN")
    http_timeout_seconds: float = 30
    http_max_retries: int = 2
    http_retry_delay_seconds: float = 2
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_timezone: str = "Asia/Ho_Chi_Minh"

    post_url: str | None = Field(default=None, alias="POST")
    post_source_url: str | None = Field(default=None, alias="POST_SOURCE")
    source_group_url: str | None = Field(default=None, alias="SOURCE_GROUP")
    holder_url: str | None = Field(default=None, alias="HOLDER")
    subsidiaries_url: str | None = Field(default=None, alias="SUBSIDIARIES")
    finance_url: str | None = Field(default=None, alias="FiNANCE_URL2")
    all_symbol_url: str | None = Field(default=None, alias="ALL_SYMBOL_URL2")
    market_mention_url: str | None = Field(default=None, alias="MARKET_MENTION")
    session_quote_url: str | None = Field(default=None, alias="BUY_SELL_DURING_SESSION")

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="finance123456", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
