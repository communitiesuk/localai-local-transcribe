"""Merge analytics and auth email migration heads.

Revision ID: c0a7c3be4d12
Revises: 7c4d81ea60b3, a3bcafd96ae9
Create Date: 2026-09-23 14:35:00.000000

"""

from typing import Sequence

# revision identifiers, used by Alembic.
revision = "c0a7c3be4d12"
down_revision = ("7c4d81ea60b3", "a3bcafd96ae9")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
