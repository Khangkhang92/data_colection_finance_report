"""add new_posts_content table

Revision ID: 20260512_0005
Revises: 20260512_0004
Create Date: 2026-05-12 03:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260512_0005"
down_revision = "20260512_0004"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _has_index(table_name: str, index_name: str) -> bool:
    insp = inspect(op.get_bind())
    return any(ix.get("name") == index_name for ix in insp.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("new_posts_content"):
        op.create_table(
            "new_posts_content",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("menu_name", sa.String(length=128), nullable=False),
            sa.Column("fireant_post_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=True),
            sa.Column("user_name", sa.String(length=255), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("original_content", sa.Text(), nullable=True),
            sa.Column("language", sa.String(length=32), nullable=True),
            sa.Column("post_type", sa.Integer(), nullable=True),
            sa.Column("approved", sa.Boolean(), nullable=True),
            sa.Column("is_expert_idea", sa.Boolean(), nullable=True),
            sa.Column("total_likes", sa.Integer(), nullable=True),
            sa.Column("total_replies", sa.Integer(), nullable=True),
            sa.Column("total_shares", sa.Integer(), nullable=True),
            sa.Column("post_source_url", sa.Text(), nullable=True),
            sa.Column("tagged_symbols", sa.JSON(), nullable=True),
            sa.Column("images", sa.JSON(), nullable=True),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("author", sa.String(length=255), nullable=True),
            sa.Column("source_url", sa.Text(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("menu_name", "fireant_post_id", name="uq_new_posts_content_menu_post"),
        )

    for idx, cols in [
        ("ix_new_posts_content_menu_name", ["menu_name"]),
        ("ix_new_posts_content_fireant_post_id", ["fireant_post_id"]),
        ("ix_new_posts_content_user_id", ["user_id"]),
        ("ix_new_posts_content_is_expert_idea", ["is_expert_idea"]),
        ("ix_new_posts_content_published_at", ["published_at"]),
        ("ix_new_posts_content_updated_at", ["updated_at"]),
    ]:
        if not _has_index("new_posts_content", idx):
            op.create_index(idx, "new_posts_content", cols)

    if not _has_table("new_posts_content_post_groups"):
        op.create_table(
            "new_posts_content_post_groups",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("new_post_content_id", sa.Integer(), sa.ForeignKey("new_posts_content.id"), nullable=False),
            sa.Column("post_group_id", sa.Integer(), sa.ForeignKey("post_groups.post_group_id"), nullable=False),
            sa.UniqueConstraint(
                "new_post_content_id",
                "post_group_id",
                name="uq_new_posts_content_post_group",
            ),
        )
    for idx, cols in [
        ("ix_new_posts_content_post_groups_new_post_content_id", ["new_post_content_id"]),
        ("ix_new_posts_content_post_groups_post_group_id", ["post_group_id"]),
    ]:
        if not _has_index("new_posts_content_post_groups", idx):
            op.create_index(idx, "new_posts_content_post_groups", cols)


def downgrade() -> None:
    for idx in [
        "ix_new_posts_content_post_groups_post_group_id",
        "ix_new_posts_content_post_groups_new_post_content_id",
    ]:
        if _has_index("new_posts_content_post_groups", idx):
            op.drop_index(idx, table_name="new_posts_content_post_groups")
    if _has_table("new_posts_content_post_groups"):
        op.drop_table("new_posts_content_post_groups")

    for idx in [
        "ix_new_posts_content_updated_at",
        "ix_new_posts_content_published_at",
        "ix_new_posts_content_is_expert_idea",
        "ix_new_posts_content_user_id",
        "ix_new_posts_content_fireant_post_id",
        "ix_new_posts_content_menu_name",
    ]:
        if _has_index("new_posts_content", idx):
            op.drop_index(idx, table_name="new_posts_content")
    if _has_table("new_posts_content"):
        op.drop_table("new_posts_content")
