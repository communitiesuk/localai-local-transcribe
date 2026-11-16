"""add summary analytics event types

Revision ID: 4ef0a7bae98c
Revises: 33c5c81f24f7
Create Date: 2026-11-03 14:29:55.270567

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ef0a7bae98c"
down_revision: str | None = "33c5c81f24f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Stored by name (uppercase), matching Enum(AnalyticsEventType, name="analyticseventtype").
NEW_EVENT_TYPES = (
    "SUMMARY_REQUESTED",
    "SUMMARY_EDIT_SUBMITTED",
    "SUMMARY_DOWNLOADED",
    "SUMMARY_COPIED",
)


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE is transaction-safe from Postgres 12 onwards, provided the new label is not used in
    # the same transaction. This migration inserts no rows, so that holds.
    for value in NEW_EVENT_TYPES:
        op.execute(f"ALTER TYPE analyticseventtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """No-op: Postgres cannot drop enum values, and recreating the type would rewrite analytics_event."""
