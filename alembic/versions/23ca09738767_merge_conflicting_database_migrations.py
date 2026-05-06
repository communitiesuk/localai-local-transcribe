"""Merge conflicting database migrations

Revision ID: 23ca09738767
Revises: bf3e4dac2dcd, cbb794e0ad72
Create Date: 2026-05-06 16:33:47.800386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '23ca09738767'
down_revision: Union[str, None] = ('bf3e4dac2dcd', 'cbb794e0ad72')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
