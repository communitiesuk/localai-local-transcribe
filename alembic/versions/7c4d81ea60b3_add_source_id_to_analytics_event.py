"""add source id to analytics event

Revision ID: 7c4d81ea60b3
Revises: 3e9c17b4a2d8
Create Date: 2026-09-22 11:18:33.204517

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c4d81ea60b3"
down_revision: str | None = "3e9c17b4a2d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT_NAME = "uq_analytics_event_event_type_source_id"


def upgrade() -> None:
    op.add_column("analytics_event", sa.Column("source_id", sa.Uuid(), nullable=True))
    # Idempotency key for worker-recorded events, which are written before their queue message is acknowledged.
    # NULLs are distinct in Postgres, so events without a source_id are unaffected by this constraint.
    op.create_unique_constraint(CONSTRAINT_NAME, "analytics_event", ["event_type", "source_id"])


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "analytics_event", type_="unique")
    op.drop_column("analytics_event", "source_id")
