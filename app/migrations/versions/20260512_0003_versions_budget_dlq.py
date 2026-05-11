"""add versioning and dead letter

Revision ID: 20260512_0003
Revises: 20260512_0002
Create Date: 2026-05-12 01:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260512_0003"
down_revision = "20260512_0002"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(col.get("name") == column_name for col in insp.get_columns(table_name))


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _has_index(table_name: str, index_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(ix.get("name") == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    # Version fields
    for col in ["prompt_version", "embedding_version", "summary_version"]:
        if not _has_column("rag_sample_answers", col):
            op.add_column("rag_sample_answers", sa.Column(col, sa.String(length=64), nullable=True))

    for col in ["prompt_version", "embedding_version"]:
        if not _has_column("rag_query_cache", col):
            op.add_column("rag_query_cache", sa.Column(col, sa.String(length=64), nullable=True))

    if not _has_column("rag_conversation_summaries", "summary_version"):
        op.add_column("rag_conversation_summaries", sa.Column("summary_version", sa.String(length=64), nullable=True))

    # Dead-letter table
    if not _has_table("sync_dead_letter"):
        op.create_table(
            "sync_dead_letter",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("source", sa.String(length=64), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=True),
            sa.Column("entity_type", sa.String(length=64), nullable=True),
            sa.Column("entity_id", sa.String(length=128), nullable=True),
            sa.Column("action", sa.String(length=32), nullable=True),
            sa.Column("worker_name", sa.String(length=128), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    for idx, cols in [
        ("ix_sync_dead_letter_source", ["source"]),
        ("ix_sync_dead_letter_event_id", ["event_id"]),
        ("ix_sync_dead_letter_entity_type", ["entity_type"]),
        ("ix_sync_dead_letter_entity_id", ["entity_id"]),
        ("ix_sync_dead_letter_action", ["action"]),
        ("ix_sync_dead_letter_created_at", ["created_at"]),
    ]:
        if not _has_index("sync_dead_letter", idx):
            op.create_index(idx, "sync_dead_letter", cols)


def downgrade() -> None:
    for idx in [
        "ix_sync_dead_letter_created_at",
        "ix_sync_dead_letter_action",
        "ix_sync_dead_letter_entity_id",
        "ix_sync_dead_letter_entity_type",
        "ix_sync_dead_letter_event_id",
        "ix_sync_dead_letter_source",
    ]:
        if _has_index("sync_dead_letter", idx):
            op.drop_index(idx, table_name="sync_dead_letter")
    if _has_table("sync_dead_letter"):
        op.drop_table("sync_dead_letter")

    if _has_column("rag_conversation_summaries", "summary_version"):
        op.drop_column("rag_conversation_summaries", "summary_version")

    for col in ["embedding_version", "prompt_version"]:
        if _has_column("rag_query_cache", col):
            op.drop_column("rag_query_cache", col)

    for col in ["summary_version", "embedding_version", "prompt_version"]:
        if _has_column("rag_sample_answers", col):
            op.drop_column("rag_sample_answers", col)
