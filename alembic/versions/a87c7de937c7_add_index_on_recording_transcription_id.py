"""Add index on recording.transcription_id

Revision ID: a87c7de937c7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-07 15:59:35.984920

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a87c7de937c7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(op.f("ix_recording_transcription_id"), "recording", ["transcription_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recording_transcription_id"), table_name="recording")
