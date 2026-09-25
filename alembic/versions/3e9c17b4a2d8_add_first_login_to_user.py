"""add first login to user

Revision ID: 3e9c17b4a2d8
Revises: 267b146310a0
Create Date: 2026-09-21 09:41:12.583914

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e9c17b4a2d8"
down_revision: str | None = "267b146310a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user", sa.Column("first_login", sa.TIMESTAMP(timezone=True), nullable=True))
    # Existing users have already authenticated, so treat their last known login as their first. Without this
    # they would each emit a USER_FIRST_AUTHENTICATED event on their next request, long after the fact.
    op.execute('UPDATE "user" SET first_login = last_login')


def downgrade() -> None:
    op.drop_column("user", "first_login")
