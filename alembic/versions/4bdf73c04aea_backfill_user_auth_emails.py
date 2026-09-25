"""backfill user auth emails

Revision ID: 4bdf73c04aea
Revises: a3bcafd96ae9
Create Date: 2026-09-25 10:33:37.980573

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "4bdf73c04aea"
down_revision: Union[str, None] = "a3bcafd96ae9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Manual backfill of existing user email addresses
    op.execute("""
        INSERT INTO user_auth_email (user_id, email)
        SELECT id, email
        FROM "user"
        ON CONFLICT (email) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM user_auth_email
        WHERE (user_id, email) IN (
            SELECT id, email
            FROM "user"
        )
    """)
