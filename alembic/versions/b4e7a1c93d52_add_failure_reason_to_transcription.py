"""add failure_reason to transcription

Revision ID: b4e7a1c93d52
Revises: 2d900b3dd86e
Create Date: 2026-11-16 11:04:22.517903

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e7a1c93d52"
down_revision: str | None = "2d900b3dd86e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

transcription_failure_reason_enum = sa.Enum("NO_SPEECH_DETECTED", "ERROR", name="transcriptionfailurereason")


def upgrade() -> None:
    transcription_failure_reason_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "transcription",
        sa.Column(
            "failure_reason",
            postgresql.ENUM(name="transcriptionfailurereason", create_type=False),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("transcription", "failure_reason")
    transcription_failure_reason_enum.drop(op.get_bind(), checkfirst=True)
