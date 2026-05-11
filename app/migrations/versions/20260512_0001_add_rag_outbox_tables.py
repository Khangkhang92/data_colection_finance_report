"""add rag/outbox tables

Revision ID: 20260512_0001
Revises: 
Create Date: 2026-05-12 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260512_0001"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _has_index(table_name: str, index_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(ix.get("name") == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("sync_outbox"):
        op.create_table(
            "sync_outbox",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=128), nullable=False),
            sa.Column("action", sa.String(length=32), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.Column("locked_at", sa.DateTime(), nullable=True),
            sa.Column("lock_owner", sa.String(length=128), nullable=True),
        )
    if not _has_index("sync_outbox", "ix_sync_outbox_entity_type"):
        op.create_index("ix_sync_outbox_entity_type", "sync_outbox", ["entity_type"])
    if not _has_index("sync_outbox", "ix_sync_outbox_entity_id"):
        op.create_index("ix_sync_outbox_entity_id", "sync_outbox", ["entity_id"])
    if not _has_index("sync_outbox", "ix_sync_outbox_action"):
        op.create_index("ix_sync_outbox_action", "sync_outbox", ["action"])
    if not _has_index("sync_outbox", "ix_sync_outbox_status"):
        op.create_index("ix_sync_outbox_status", "sync_outbox", ["status"])

    if not _has_table("rag_sample_questions"):
        op.create_table(
            "rag_sample_questions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("normalized_question", sa.String(length=512), nullable=False),
            sa.Column("intent", sa.String(length=64), nullable=True),
            sa.Column("tickers", sa.JSON(), nullable=True),
            sa.Column("entities", sa.JSON(), nullable=True),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    if not _has_index("rag_sample_questions", "ix_rag_sample_questions_normalized_question"):
        op.create_index("ix_rag_sample_questions_normalized_question", "rag_sample_questions", ["normalized_question"])
    if not _has_index("rag_sample_questions", "ix_rag_sample_questions_priority"):
        op.create_index("ix_rag_sample_questions_priority", "rag_sample_questions", ["priority"])

    if not _has_table("rag_sample_answers"):
        op.create_table(
            "rag_sample_answers",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("sample_question_id", sa.Integer(), sa.ForeignKey("rag_sample_questions.id"), nullable=False),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("citations", sa.JSON(), nullable=True),
            sa.Column("context_refs", sa.JSON(), nullable=True),
            sa.Column("model_name", sa.String(length=128), nullable=True),
            sa.Column("version", sa.String(length=64), nullable=True),
            sa.Column("generated_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    if not _has_index("rag_sample_answers", "ix_rag_sample_answers_sample_question_id"):
        op.create_index("ix_rag_sample_answers_sample_question_id", "rag_sample_answers", ["sample_question_id"])

    if not _has_table("rag_query_cache"):
        op.create_table(
            "rag_query_cache",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("normalized_query", sa.String(length=512), nullable=False),
            sa.Column("question_hash", sa.String(length=64), nullable=False),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("citations", sa.JSON(), nullable=True),
            sa.Column("model_name", sa.String(length=128), nullable=True),
            sa.Column("generated_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("normalized_query", name="uq_rag_query_cache_normalized_query"),
            sa.UniqueConstraint("question_hash", name="uq_rag_query_cache_question_hash"),
        )
    if not _has_index("rag_query_cache", "ix_rag_query_cache_normalized_query"):
        op.create_index("ix_rag_query_cache_normalized_query", "rag_query_cache", ["normalized_query"])
    if not _has_index("rag_query_cache", "ix_rag_query_cache_question_hash"):
        op.create_index("ix_rag_query_cache_question_hash", "rag_query_cache", ["question_hash"])

    if not _has_table("rag_query_analytics"):
        op.create_table(
            "rag_query_analytics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("normalized_query", sa.String(length=512), nullable=False),
            sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_latency_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("last_seen_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("normalized_query", name="uq_rag_query_analytics_normalized_query"),
        )
    if not _has_index("rag_query_analytics", "ix_rag_query_analytics_normalized_query"):
        op.create_index("ix_rag_query_analytics_normalized_query", "rag_query_analytics", ["normalized_query"])

    if not _has_table("rag_conversation_summaries"):
        op.create_table(
            "rag_conversation_summaries",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("conversation_id", sa.String(length=128), nullable=False),
            sa.Column("user_id", sa.String(length=128), nullable=True),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("important_tickers", sa.JSON(), nullable=True),
            sa.Column("important_entities", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    if not _has_index("rag_conversation_summaries", "ix_rag_conversation_summaries_conversation_id"):
        op.create_index("ix_rag_conversation_summaries_conversation_id", "rag_conversation_summaries", ["conversation_id"])
    if not _has_index("rag_conversation_summaries", "ix_rag_conversation_summaries_user_id"):
        op.create_index("ix_rag_conversation_summaries_user_id", "rag_conversation_summaries", ["user_id"])


def downgrade() -> None:
    for idx in [
        "ix_rag_conversation_summaries_user_id",
        "ix_rag_conversation_summaries_conversation_id",
    ]:
        if _has_index("rag_conversation_summaries", idx):
            op.drop_index(idx, table_name="rag_conversation_summaries")
    if _has_table("rag_conversation_summaries"):
        op.drop_table("rag_conversation_summaries")

    if _has_index("rag_query_analytics", "ix_rag_query_analytics_normalized_query"):
        op.drop_index("ix_rag_query_analytics_normalized_query", table_name="rag_query_analytics")
    if _has_table("rag_query_analytics"):
        op.drop_table("rag_query_analytics")

    for idx in ["ix_rag_query_cache_question_hash", "ix_rag_query_cache_normalized_query"]:
        if _has_index("rag_query_cache", idx):
            op.drop_index(idx, table_name="rag_query_cache")
    if _has_table("rag_query_cache"):
        op.drop_table("rag_query_cache")

    if _has_index("rag_sample_answers", "ix_rag_sample_answers_sample_question_id"):
        op.drop_index("ix_rag_sample_answers_sample_question_id", table_name="rag_sample_answers")
    if _has_table("rag_sample_answers"):
        op.drop_table("rag_sample_answers")

    for idx in ["ix_rag_sample_questions_priority", "ix_rag_sample_questions_normalized_question"]:
        if _has_index("rag_sample_questions", idx):
            op.drop_index(idx, table_name="rag_sample_questions")
    if _has_table("rag_sample_questions"):
        op.drop_table("rag_sample_questions")

    for idx in [
        "ix_sync_outbox_status",
        "ix_sync_outbox_action",
        "ix_sync_outbox_entity_id",
        "ix_sync_outbox_entity_type",
    ]:
        if _has_index("sync_outbox", idx):
            op.drop_index(idx, table_name="sync_outbox")
    if _has_table("sync_outbox"):
        op.drop_table("sync_outbox")
