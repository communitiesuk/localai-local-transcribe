"""add unique constraint to user email

Revision ID: 5c1e1d353f2a
Revises: aeda129e5d02
Create Date: 2026-06-17 16:23:53.747727

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "5c1e1d353f2a"
down_revision: Union[str, None] = "aeda129e5d02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_user_email"), table_name="user")

    # Delete child records belonging to the newer duplicate user
    for table in ("transcription", "recording", "user_template"):
        op.execute(f"""
            DELETE FROM "{table}"
            WHERE user_id IN (
                SELECT a.id
                FROM "user" a
                JOIN "user" b
                  ON LOWER(a.email) = LOWER(b.email)
                 AND a.created_datetime > b.created_datetime
            )
        """)

    # Deletes the newer duplicate user
    op.execute("""
        DELETE FROM "user" a
        USING "user" b
        WHERE LOWER(a.email) = LOWER(b.email)
          AND a.created_datetime > b.created_datetime
    """)

    # Enforces future case-insensitive uniqueness
    op.execute("""
        CREATE UNIQUE INDEX ix_user_email_lower
        ON "user" (LOWER(email))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_email_lower")

    op.create_index(
        op.f("ix_user_email"),
        "user",
        ["email"],
        unique=False,
    )
    # Note: deletions performed during upgrade() are not restored on downgrade.
