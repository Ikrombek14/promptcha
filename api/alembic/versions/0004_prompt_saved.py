"""Tarix va kutubxona: prompts.is_saved, prompts.score, (user_id, created_at) indeksi

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX_NAME = "ix_prompts_user_created"


def _prompt_columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("prompts")}


def _prompt_indexes() -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes("prompts")}


def upgrade() -> None:
    columns = _prompt_columns()
    if "is_saved" not in columns:
        op.add_column(
            "prompts",
            sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "score" not in columns:
        op.add_column("prompts", sa.Column("score", sa.Integer(), nullable=True))
    # Tarix/kutubxona roʻyxati: user_id boʻyicha filtr + created_at boʻyicha tartib
    if INDEX_NAME not in _prompt_indexes():
        op.create_index(INDEX_NAME, "prompts", ["user_id", "created_at"])


def downgrade() -> None:
    if INDEX_NAME in _prompt_indexes():
        op.drop_index(INDEX_NAME, table_name="prompts")
    columns = _prompt_columns()
    if "score" in columns:
        op.drop_column("prompts", "score")
    if "is_saved" in columns:
        op.drop_column("prompts", "is_saved")
