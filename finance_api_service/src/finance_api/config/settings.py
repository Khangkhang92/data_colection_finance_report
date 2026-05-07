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
    symbol_detail_url: str = Field(
        default="https://api.fireant.vn/symbols/{symbol}",
        alias="SYMBOL_DETAIL_URL",
    )
    symbol_fundamental_url: str = Field(
        default="https://api.fireant.vn/symbols/{symbol}/fundamental",
        alias="SYMBOL_FUNDAMENTAL_URL",
    )
    symbol_historical_quotes_url: str = Field(
        default="https://api.fireant.vn/symbols/{symbol}/historical-quotes",
        alias="SYMBOL_HISTORICAL_QUOTES_URL",
    )
    symbol_search_url: str = Field(
        default="https://api.fireant.vn/symbols/search",
        alias="SYMBOL_SEARCH_URL",
    )
    symbol_movers_url: str = Field(
        default="https://api.fireant.vn/symbols/movers",
        alias="SYMBOL_MOVERS_URL",
    )
    symbol_warrant_info_url: str = Field(
        default="https://api.fireant.vn/symbols/{symbol}/warrant-info",
        alias="SYMBOL_WARRANT_INFO_URL",
    )
    mxv_contracts_url: str = Field(
        default="https://api.fireant.vn/mxv/market/contracts",
        alias="MXV_CONTRACTS_URL",
    )
    industries_url: str = Field(default="https://api.fireant.vn/industries", alias="INDUSTRIES_URL")
    industry_symbols_url: str = Field(
        default="https://api.fireant.vn/icb/{industry_code}/symbols",
        alias="INDUSTRY_SYMBOLS_URL",
    )
    market_mention_url: str | None = Field(default=None, alias="MARKET_MENTION")
    session_quote_url: str | None = Field(default=None, alias="BUY_SELL_DURING_SESSION")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
