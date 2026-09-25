"""merge analytics event and auth email backfill heads

Revision ID: 473aa38c0de8
Revises: 4bdf73c04aea, 7c4d81ea60b3
Create Date: 2026-09-25 12:10:01.512858

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "473aa38c0de8"
down_revision: str | None = ("4bdf73c04aea", "7c4d81ea60b3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
