"""outbox retry hardening

Revision ID: 20260512_0002
Revises: 20260512_0001
Create Date: 2026-05-12 00:30:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260512_0002"
down_revision = "20260512_0001"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(col.get("name") == column_name for col in insp.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(ix.get("name") == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if _has_column("sync_outbox", "max_retries") is False:
        op.add_column("sync_outbox", sa.Column("max_retries", sa.Integer(), nullable=False, server_default="5"))
    if _has_column("sync_outbox", "next_retry_at") is False:
        op.add_column("sync_outbox", sa.Column("next_retry_at", sa.DateTime(), nullable=True))

    if not _has_index("sync_outbox", "ix_sync_outbox_next_retry_at"):
        op.create_index("ix_sync_outbox_next_retry_at", "sync_outbox", ["next_retry_at"])
    if not _has_index("sync_outbox", "ix_sync_outbox_status_created_at"):
        op.create_index("ix_sync_outbox_status_created_at", "sync_outbox", ["status", "created_at"])
    if not _has_index("sync_outbox", "ix_sync_outbox_status_entity_action_created"):
        op.create_index(
            "ix_sync_outbox_status_entity_action_created",
            "sync_outbox",
            ["status", "entity_type", "action", "created_at"],
        )


def downgrade() -> None:
    for idx in [
        "ix_sync_outbox_status_entity_action_created",
        "ix_sync_outbox_status_created_at",
        "ix_sync_outbox_next_retry_at",
    ]:
        if _has_index("sync_outbox", idx):
            op.drop_index(idx, table_name="sync_outbox")

    if _has_column("sync_outbox", "next_retry_at"):
        op.drop_column("sync_outbox", "next_retry_at")
    if _has_column("sync_outbox", "max_retries"):
        op.drop_column("sync_outbox", "max_retries")
