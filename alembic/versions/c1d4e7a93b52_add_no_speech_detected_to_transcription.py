"""add no_speech_detected to transcription

Revision ID: c1d4e7a93b52
Revises: 33c5c81f24f7
Create Date: 2026-11-10 10:12:04.118320

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c1d4e7a93b52"
down_revision: Union[str, None] = "33c5c81f24f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transcription",
        sa.Column("no_speech_detected", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("transcription", "no_speech_detected")
