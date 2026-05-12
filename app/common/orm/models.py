from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Symbol(Base):
    __tablename__ = "symbols"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    exchange: Mapped[str | None] = mapped_column(String(32), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    short_industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cap_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)


class PostGroup(Base):
    __tablename__ = "post_groups"

    post_group_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fireant_post_group_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    @staticmethod
    def from_json(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "fireant_post_group_id": data.get("id") or data.get("postGroupID") or 0,
            "name": data.get("name") or data.get("title"),
        }


class PostSource(Base):
    __tablename__ = "post_sources"

    post_source_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fireant_post_source_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    @staticmethod
    def from_json(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "fireant_post_source_id": data.get("id") or data.get("postSourceID") or 0,
            "name": data.get("name") or data.get("title"),
        }


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fireant_post_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    post_group_id: Mapped[int | None] = mapped_column(ForeignKey("post_groups.post_group_id"), nullable=True)
    post_source_id: Mapped[int | None] = mapped_column(ForeignKey("post_sources.post_source_id"), nullable=True)

    @staticmethod
    def from_json(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "fireant_post_id": data.get("id") or data.get("postID") or 0,
            "title": data.get("title"),
            "content": data.get("content") or data.get("description"),
            "published_at": None,
        }


class TaggedSymbol(Base):
    __tablename__ = "tagged_symbols"
    __table_args__ = (UniqueConstraint("post_id", "symbol_ticker", name="uq_tagged_symbol_post_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.post_id"), nullable=False)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)


class MajorHolder(Base):
    __tablename__ = "major_holders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shares: Mapped[float | None] = mapped_column(Float, nullable=True)
    ownership: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_organization: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_foreigner: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_foundation: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_listing: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    listing_symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reported: Mapped[date | None] = mapped_column(Date, nullable=True)


class Subsidiaries(Base):
    __tablename__ = "subsidiaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)
    sub_symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    short_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    international_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ownership: Mapped[float | None] = mapped_column(Float, nullable=True)
    shares: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_listed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    charter_capital: Mapped[float | None] = mapped_column(Float, nullable=True)


class MarketMention(Base):
    __tablename__ = "market_mentions"
    __table_args__ = (UniqueConstraint("symbol_ticker", "date", name="uq_market_mentions_symbol_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    month_color: Mapped[str | None] = mapped_column(String(32), nullable=True)


class SessionQuote(Base):
    __tablename__ = "session_quotes"
    __table_args__ = (UniqueConstraint("symbol_ticker", "datetime", name="uq_session_quotes_symbol_datetime"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)
    side: Mapped[str | None] = mapped_column(String(32), nullable=True)
    match_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class HistoryPrice(Base):
    __tablename__ = "history_prices"
    __table_args__ = (UniqueConstraint("symbol_ticker", "date", name="uq_history_prices_symbol_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    price_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_open: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_basic: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    deal_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    putthrough_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    putthrough_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_foreign_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_foreign_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_foreign_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_foreign_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    adj_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_foreign_room: Mapped[float | None] = mapped_column(Float, nullable=True)
    prop_trading_net_deal_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    prop_trading_net_pt_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    prop_trading_net_value: Mapped[float | None] = mapped_column(Float, nullable=True)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("name", "symbol_ticker", name="uq_reports_name_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker: Mapped[str] = mapped_column(ForeignKey("symbols.ticker"), nullable=False)
    type: Mapped[int] = mapped_column(Integer, nullable=False)
    lever: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Data(Base):
    __tablename__ = "report_data"
    __table_args__ = (UniqueConstraint("report_id", "quarter", "year", name="uq_report_data_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)


class NewPostsContent(Base):
    __tablename__ = "new_posts_content"
    __table_args__ = (
        UniqueConstraint("menu_name", "fireant_post_id", name="uq_new_posts_content_menu_post"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    fireant_post_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    post_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_expert_idea: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    total_likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_replies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    post_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tagged_symbols: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    images: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class NewPostsContentPostGroup(Base):
    __tablename__ = "new_posts_content_post_groups"
    __table_args__ = (
        UniqueConstraint(
            "new_post_content_id",
            "post_group_id",
            name="uq_new_posts_content_post_group",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    new_post_content_id: Mapped[int] = mapped_column(
        ForeignKey("new_posts_content.id"),
        nullable=False,
        index=True,
    )
    post_group_id: Mapped[int] = mapped_column(
        ForeignKey("post_groups.post_group_id"),
        nullable=False,
        index=True,
    )


class DetailNewPost(Base):
    __tablename__ = "detail_new_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    new_post_content_id: Mapped[int] = mapped_column(
        ForeignKey("new_posts_content.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    fireant_post_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    detail_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_original_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class SyncOutbox(Base):
    __tablename__ = "sync_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lock_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class RagSampleQuestion(Base):
    __tablename__ = "rag_sample_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_question: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tickers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    entities: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RagSampleAnswer(Base):
    __tablename__ = "rag_sample_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sample_question_id: Mapped[int] = mapped_column(
        ForeignKey("rag_sample_questions.id"),
        nullable=False,
        index=True,
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    context_refs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RagQueryCache(Base):
    __tablename__ = "rag_query_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    normalized_query: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    question_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RagQueryAnalytics(Base):
    __tablename__ = "rag_query_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    normalized_query: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RagConversationSummary(Base):
    __tablename__ = "rag_conversation_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    important_tickers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    important_entities: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    summary_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RagChatMessage(Base):
    __tablename__ = "rag_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class SyncDeadLetter(Base):
    __tablename__ = "sync_dead_letter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    worker_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
