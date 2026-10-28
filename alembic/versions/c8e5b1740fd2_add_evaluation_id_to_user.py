"""add evaluation id to user

Revision ID: c8e5b1740fd2
Revises: a87c7de937c7
Create Date: 2026-09-08 10:12:04.318920

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8e5b1740fd2"
down_revision: str | None = "a87c7de937c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT_NAME = "uq_user_evaluation_id"


def upgrade() -> None:
    op.add_column("user", sa.Column("evaluation_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_unique_constraint(CONSTRAINT_NAME, "user", ["evaluation_id"])


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "user", type_="unique")
    op.drop_column("user", "evaluation_id")
