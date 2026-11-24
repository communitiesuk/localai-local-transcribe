"""backfill blank transcript titles

Revision ID: 411a5105c9b5
Revises: d9c3f5a71e46
Create Date: 2026-11-24 19:48:16.606129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '411a5105c9b5'
down_revision: Union[str, None] = 'd9c3f5a71e46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Manual edit to make '' titles null
    op.execute("""
        UPDATE transcription
        SET title = NULL
        WHERE title IS NOT NULL
        AND btrim(title) = ''
    """)


def downgrade() -> None:
    pass
