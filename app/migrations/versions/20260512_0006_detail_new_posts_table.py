"""add detail_new_posts table

Revision ID: 20260512_0006
Revises: 20260512_0005
Create Date: 2026-05-12 15:45:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260512_0006"
down_revision = "20260512_0005"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _has_index(table_name: str, index_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(ix.get("name") == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("detail_new_posts"):
        op.create_table(
            "detail_new_posts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("new_post_content_id", sa.Integer(), sa.ForeignKey("new_posts_content.id"), nullable=False),
            sa.Column("fireant_post_id", sa.Integer(), nullable=False),
            sa.Column("detail_content", sa.Text(), nullable=True),
            sa.Column("detail_original_content", sa.Text(), nullable=True),
            sa.Column("detail_summary", sa.Text(), nullable=True),
            sa.Column("detail_payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("new_post_content_id", name="uq_detail_new_posts_new_post_content_id"),
            sa.UniqueConstraint("fireant_post_id", name="uq_detail_new_posts_fireant_post_id"),
        )

    for idx, cols in [
        ("ix_detail_new_posts_new_post_content_id", ["new_post_content_id"]),
        ("ix_detail_new_posts_fireant_post_id", ["fireant_post_id"]),
        ("ix_detail_new_posts_updated_at", ["updated_at"]),
    ]:
        if not _has_index("detail_new_posts", idx):
            op.create_index(idx, "detail_new_posts", cols)


def downgrade() -> None:
    for idx in [
        "ix_detail_new_posts_updated_at",
        "ix_detail_new_posts_fireant_post_id",
        "ix_detail_new_posts_new_post_content_id",
    ]:
        if _has_index("detail_new_posts", idx):
            op.drop_index(idx, table_name="detail_new_posts")
    if _has_table("detail_new_posts"):
        op.drop_table("detail_new_posts")
