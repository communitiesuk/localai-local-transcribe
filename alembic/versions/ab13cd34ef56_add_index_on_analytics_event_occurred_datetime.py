"""add index on analytics event occurred datetime

Revision ID: ab13cd34ef56
Revises: 7c4d81ea60b3
Create Date: 2026-10-05 10:40:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ab13cd34ef56"
down_revision: str | None = "7c4d81ea60b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_analytics_event_occurred_datetime"),
        "analytics_event",
        ["occurred_datetime"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_analytics_event_occurred_datetime"), table_name="analytics_event")
