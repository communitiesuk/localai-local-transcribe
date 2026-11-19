"""add tou accepted analytics event type

Revision ID: 7c1d9ab35e42
Revises: 4ef0a7bae98c
Create Date: 2026-11-04 15:12:08.441920

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c1d9ab35e42"
down_revision: str | None = "4ef0a7bae98c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Stored by name (uppercase), matching Enum(AnalyticsEventType, name="analyticseventtype").
NEW_EVENT_TYPE = "TOU_ACCEPTED"


def upgrade() -> None:
    # A separate revision from the summary event types rather than another entry in that migration's tuple: Alembic
    # will not re-run an already-stamped revision and the downgrade below is a no-op, so any database that has
    # already upgraded past 4ef0a7bae98c would otherwise never receive this label.
    op.execute(f"ALTER TYPE analyticseventtype ADD VALUE IF NOT EXISTS '{NEW_EVENT_TYPE}'")


def downgrade() -> None:
    """No-op: Postgres cannot drop enum values, and recreating the type would rewrite analytics_event."""
