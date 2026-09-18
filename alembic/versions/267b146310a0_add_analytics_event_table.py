"""add analytics event table

Revision ID: 267b146310a0
Revises: b6a9d4f37c21
Create Date: 2026-09-17 11:02:49.394856

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "267b146310a0"
down_revision: str | None = "b6a9d4f37c21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

analytics_event_type_enum = sa.Enum(
    "USER_INVITED",
    "USER_AUTHENTICATED",
    "USER_DELETED",
    "AUDIO_UPLOAD_STARTED",
    "AUDIO_UPLOAD_COMPLETED",
    "SUMMARY_RECEIVED",
    "TRANSCRIPTION_RECEIVED",
    "TRANSCRIPTION_EDIT_SUBMITTED",
    name="analyticseventtype",
)


def upgrade() -> None:
    op.create_table(
        "analytics_event",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("occurred_datetime", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("event_type", analytics_event_type_enum, nullable=False),
        sa.Column("evaluation_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("recording_id", sa.Uuid(), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analytics_event_evaluation_id"), "analytics_event", ["evaluation_id"], unique=False)
    op.create_index(op.f("ix_analytics_event_recording_id"), "analytics_event", ["recording_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analytics_event_recording_id"), table_name="analytics_event")
    op.drop_index(op.f("ix_analytics_event_evaluation_id"), table_name="analytics_event")
    op.drop_table("analytics_event")
    analytics_event_type_enum.drop(op.get_bind(), checkfirst=True)
