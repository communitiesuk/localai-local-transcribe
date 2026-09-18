"""Add guardrail_failure_category table

Revision ID: 5e6494b47452
Revises: a87c7de937c7
Create Date: 2026-09-16 12:40:42.684914

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5e6494b47452"
down_revision: str | None = "a87c7de937c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guardrail_failure_category",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_datetime", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_datetime", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("guardrail_result_id", sa.UUID(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("explanation", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["guardrail_result_id"], ["guardrail_result.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guardrail_failure_category_category"),
        "guardrail_failure_category",
        ["category"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_guardrail_failure_category_category"),
        table_name="guardrail_failure_category",
    )
    op.drop_table("guardrail_failure_category")
