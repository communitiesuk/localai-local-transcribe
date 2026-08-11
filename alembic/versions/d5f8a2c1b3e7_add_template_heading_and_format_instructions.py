"""Add template heading and section format instructions

Revision ID: d5f8a2c1b3e7
Revises: 1807abaec3b8
Create Date: 2026-08-05 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlmodel import AutoString

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5f8a2c1b3e7"
down_revision: str | None = "1807abaec3b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_template",
        sa.Column("heading", AutoString(), nullable=False, server_default=""),
    )
    op.add_column(
        "template_question",
        sa.Column("format_instructions", AutoString(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("template_question", "format_instructions")
    op.drop_column("user_template", "heading")
