"""backfill default template ids

Revision ID: 7d7300906f79
Revises: 33c5c81f24f7
Create Date: 2026-11-12 14:24:27.827844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7d7300906f79'
down_revision: Union[str, None] = '33c5c81f24f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Manual backfill of defualt templates with template IDs in the format "default-<template-name>"
    op.execute(
        """
        UPDATE analytics_event AS event
        SET event_metadata = event.event_metadata || jsonb_build_object(
            'template_id',
            CASE lower(minute.template_name)
                WHEN 'general' THEN 'default-general'
                WHEN 'form b' THEN 'default-form-b'
                WHEN 'housing application form' THEN 'default-housing-application-form'
                WHEN 'personalised housing plan' THEN 'default-personalised-housing-plan'
                WHEN 'triage assessment' THEN 'default-triage-assessment'
                WHEN 'quick note' THEN 'default-quick-note'
            END,
            'template_source',
            'default'
        )
        FROM minute_version
        JOIN minute ON minute.id = minute_version.minute_id
        WHERE event.event_type = 'SUMMARY_RECEIVED'
          AND event.source_id = minute_version.id
          AND minute.user_template_id IS NULL
          AND event.event_metadata->'template_id' = 'null'::jsonb
          AND lower(minute.template_name) IN (
            'general',
            'form b',
            'housing application form',
            'personalised housing plan',
            'triage assessment',
            'quick note'
          )
        """
    )


def downgrade() -> None:
    pass
