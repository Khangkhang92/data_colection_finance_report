from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[4]
_SERVICE_ROOT = _PROJECT_ROOT / "app" / "services" / "finance_rag_service"


class Settings(BaseSettings):
    app_name: str = "finance-rag-chat"
    app_env: str = "dev"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    novita_api_key: str = ""
    novita_base_url: str = ""
    novita_model: str = "deepseek/deepseek-v3-turbo"
    openai_base_url: str = ""

    rag_doc_path: str = "data/finance_docs.md"
    max_context_chunks: int = 4
    vector_backend: str = "qdrant"
    graph_backend: str = "neo4j"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "finance_docs"
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="finance123456", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    embedding_model: str = "text-embedding-3-small"
    redis_url: str = "redis://localhost:6379/0"
    prompt_version: str = "v1"
    embedding_version: str = "v1"
    summary_version: str = "v1"
    max_context_tokens: int = 6000
    max_vector_context_tokens: int = 3500
    max_graph_context_tokens: int = 2000

    model_config = SettingsConfigDict(
        env_file=(str(_PROJECT_ROOT / ".env"), str(_SERVICE_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
