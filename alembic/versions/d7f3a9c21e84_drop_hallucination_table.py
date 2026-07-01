"""drop hallucination table

Revision ID: d7f3a9c21e84
Revises: f4510d2ab4af
Create Date: 2026-06-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7f3a9c21e84"
down_revision: str | None = "f4510d2ab4af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

hallucination_type_enum = sa.Enum(
    "FACTUAL_FABRICATION", "NONSENSICAL", "CONTRADICTION", "MISLEADING", "OTHER", name="hallucinationtype"
)


def upgrade() -> None:
    op.drop_table("hallucination")
    hallucination_type_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    hallucination_type_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "hallucination",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_datetime", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_datetime", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("minute_version_id", sa.Uuid(), nullable=False),
        sa.Column("hallucination_type", hallucination_type_enum, nullable=False),
        sa.Column("hallucination_text", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("hallucination_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["minute_version_id"], ["minute_version.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
