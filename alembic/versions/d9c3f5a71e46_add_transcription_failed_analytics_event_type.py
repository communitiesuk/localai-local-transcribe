"""add transcription failed analytics event type

Revision ID: d9c3f5a71e46
Revises: b4e7a1c93d52
Create Date: 2026-11-16 11:06:49.223140

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9c3f5a71e46"
down_revision: str | None = "b4e7a1c93d52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Stored by name (uppercase), matching Enum(AnalyticsEventType, name="analyticseventtype").
NEW_EVENT_TYPE = "TRANSCRIPTION_FAILED"


def upgrade() -> None:
    op.execute(f"ALTER TYPE analyticseventtype ADD VALUE IF NOT EXISTS '{NEW_EVENT_TYPE}'")


def downgrade() -> None:
    """No-op: Postgres cannot drop enum values, and recreating the type would rewrite analytics_event."""
