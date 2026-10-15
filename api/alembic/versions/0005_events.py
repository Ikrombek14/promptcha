"""Hodisalar jurnali (events) va promptga feedback/criteria ustunlari

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _prompt_columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("prompts")}


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    if "events" not in _tables():
        op.create_table(
            "events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("guest_id", sa.String(64), nullable=True),
            sa.Column("session_id", sa.String(64), nullable=True),
            sa.Column("name", sa.String(48), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_events_user_id", "events", ["user_id"])
        op.create_index("ix_events_guest_id", "events", ["guest_id"])
        op.create_index("ix_events_created_at", "events", ["created_at"])
        op.create_index("ix_events_name_created", "events", ["name", "created_at"])
        op.create_index("ix_events_session", "events", ["session_id", "created_at"])

    cols = _prompt_columns()
    if "criteria" not in cols:
        op.add_column("prompts", sa.Column("criteria", sa.JSON(), nullable=True))
    if "feedback" not in cols:
        op.add_column("prompts", sa.Column("feedback", sa.String(16), nullable=True))
    if "feedback_note" not in cols:
        op.add_column("prompts", sa.Column("feedback_note", sa.Text(), nullable=True))


def downgrade() -> None:
    cols = _prompt_columns()
    for name in ("feedback_note", "feedback", "criteria"):
        if name in cols:
            op.drop_column("prompts", name)
    if "events" in _tables():
        op.drop_table("events")
