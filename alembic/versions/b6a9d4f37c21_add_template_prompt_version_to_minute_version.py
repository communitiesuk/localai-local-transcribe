"""Add template prompt version to minute version

Revision ID: b6a9d4f37c21
Revises: c8e5b1740fd2
Create Date: 2026-09-14 12:20:20.694000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "b6a9d4f37c21"
down_revision: str | None = "c8e5b1740fd2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "minute_version",
        sa.Column("template_prompt_version", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("minute_version", "template_prompt_version")
