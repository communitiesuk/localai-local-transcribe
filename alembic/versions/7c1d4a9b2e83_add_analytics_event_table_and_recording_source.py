"""add recording source

Revision ID: 7c1d4a9b2e83
Revises: 4bdf73c04aea
Create Date: 2026-09-24 17:40:12.114927

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7c1d4a9b2e83"
down_revision: Union[str, None] = "4bdf73c04aea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    recordingsource = postgresql.ENUM(
        "LIVE_RECORDING", "DIRECT_UPLOAD", name="recordingsource", create_type=False
    )
    recordingsource.create(op.get_bind(), checkfirst=True)  # manual edit to create enum

    op.add_column("recording", sa.Column("source", recordingsource, nullable=True))


def downgrade() -> None:
    op.drop_column("recording", "source")
    sa.Enum(name="recordingsource").drop(op.get_bind(), checkfirst=True)  # manual edit to delete enum
