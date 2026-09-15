"""initial: users, user_contexts, prompts, usage_log

Revision ID: 0001
Revises:
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("google_sub", sa.String(64), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("avatar_url", sa.String(1000)),
        sa.Column("locale", sa.String(5), nullable=False, server_default="uz"),
        sa.Column("plan", sa.String(16), nullable=False, server_default="free"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="inferred"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_user_contexts_user_id", "user_contexts", ["user_id"])
    op.create_index("ix_user_contexts_user_key", "user_contexts", ["user_id", "key"], unique=True)

    op.create_table(
        "prompts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
        ),
        sa.Column("input_text", sa.Text, nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("ai", sa.String(16), nullable=False),
        sa.Column("clarifications", sa.JSON),
        sa.Column("result", sa.Text, nullable=False),
        sa.Column("explanations", sa.JSON),
        sa.Column("locale", sa.String(5), nullable=False, server_default="uz"),
        sa.Column("output_language", sa.String(5), nullable=False, server_default="en"),
        sa.Column("share_slug", sa.String(32)),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_prompts_user_id", "prompts", ["user_id"])
    op.create_index("ix_prompts_share_slug", "prompts", ["share_slug"], unique=True)
    op.create_index("ix_prompts_created_at", "prompts", ["created_at"])

    op.create_table(
        "usage_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("guest_id", sa.String(64)),
        sa.Column("action", sa.String(32), nullable=False, server_default="generate"),
        sa.Column("ai", sa.String(16)),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_usage_log_guest_id", "usage_log", ["guest_id"])
    op.create_index("ix_usage_log_user_created", "usage_log", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("usage_log")
    op.drop_table("prompts")
    op.drop_table("user_contexts")
    op.drop_table("users")
