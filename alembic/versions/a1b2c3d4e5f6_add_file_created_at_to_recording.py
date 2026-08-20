"""Add file_created_at to recording

Revision ID: a1b2c3d4e5f6
Revises: fe0e69c8d4db
Create Date: 2026-08-18 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None | tuple = ("fe0e69c8d4db", "d5f8a2c1b3e7")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recording", sa.Column("file_created_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("recording", "file_created_at")
