"""usage_log.ip — IP boʻyicha kunlik limit

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("usage_log", sa.Column("ip", sa.String(45)))
    op.create_index("ix_usage_log_ip_created", "usage_log", ["ip", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_usage_log_ip_created", table_name="usage_log")
    op.drop_column("usage_log", "ip")
