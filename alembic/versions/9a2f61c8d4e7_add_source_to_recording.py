"""add source to recording

Revision ID: 9a2f61c8d4e7
Revises: 7c4d81ea60b3
Create Date: 2026-10-06 15:12:04.118427

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a2f61c8d4e7"
down_revision: str | None = "7c4d81ea60b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

recording_source_enum = sa.Enum("LIVE_RECORDING", "DIRECT_UPLOAD", name="recordingsource")


def upgrade() -> None:
    recording_source_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "recording",
        sa.Column("source", postgresql.ENUM(name="recordingsource", create_type=False), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recording", "source")
    recording_source_enum.drop(op.get_bind(), checkfirst=True)
