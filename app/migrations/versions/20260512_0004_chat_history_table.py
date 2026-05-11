"""add rag chat history table

Revision ID: 20260512_0004
Revises: 20260512_0003
Create Date: 2026-05-12 01:20:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260512_0004"
down_revision = "20260512_0003"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _has_index(table_name: str, index_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(ix.get("name") == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("rag_chat_messages"):
        op.create_table(
            "rag_chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("conversation_id", sa.String(length=128), nullable=False),
            sa.Column("user_id", sa.String(length=128), nullable=True),
            sa.Column("role", sa.String(length=32), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("sources", sa.JSON(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    for idx, cols in [
        ("ix_rag_chat_messages_conversation_id", ["conversation_id"]),
        ("ix_rag_chat_messages_user_id", ["user_id"]),
        ("ix_rag_chat_messages_role", ["role"]),
        ("ix_rag_chat_messages_created_at", ["created_at"]),
    ]:
        if not _has_index("rag_chat_messages", idx):
            op.create_index(idx, "rag_chat_messages", cols)


def downgrade() -> None:
    for idx in [
        "ix_rag_chat_messages_created_at",
        "ix_rag_chat_messages_role",
        "ix_rag_chat_messages_user_id",
        "ix_rag_chat_messages_conversation_id",
    ]:
        if _has_index("rag_chat_messages", idx):
            op.drop_index(idx, table_name="rag_chat_messages")
    if _has_table("rag_chat_messages"):
        op.drop_table("rag_chat_messages")
