import logging
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_models import (
    ANALYTICS_EVENT_SOURCE_UNIQUE_CONSTRAINT,
    AnalyticsEvent,
    AnalyticsEventMetadata,
    AnalyticsEventType,
)

logger = logging.getLogger(__name__)


def _insert_statement(
    event_type: AnalyticsEventType,
    evaluation_id: str,
    organisation_id: UUID | None,
    recording_id: UUID | None,
    source_id: UUID | None,
    event_metadata: AnalyticsEventMetadata | None,
) -> Any:
    """Build an idempotent insert for an analytics event.

    `on_conflict_do_nothing` makes a redelivered event a no-op rather than a duplicate row. It only bites when
    `source_id` is set: Postgres treats NULLs as distinct, so events without an idempotency key always insert.
    """
    return (
        insert(AnalyticsEvent)
        .values(
            event_type=event_type,
            evaluation_id=evaluation_id,
            organisation_id=organisation_id,
            recording_id=recording_id,
            source_id=source_id,
            event_metadata=event_metadata,
        )
        .on_conflict_do_nothing(constraint=ANALYTICS_EVENT_SOURCE_UNIQUE_CONSTRAINT)
    )


async def record_analytics_event(
    session: AsyncSession,
    event_type: AnalyticsEventType,
    evaluation_id: str | None,
    organisation_id: UUID | None,
    recording_id: UUID | None = None,
    source_id: UUID | None = None,
    event_metadata: AnalyticsEventMetadata | None = None,
) -> None:
    """Record a first-party analytics event (see ADR-028).

    Recording analytics must never break the primary user journey, so any failure here is logged and swallowed
    rather than propagated. Users without an evaluation_id (e.g. legacy accounts) are skipped, as there is no
    pseudonymous identifier to report against.

    `organisation_id` is stored so events can be reported per local authority. It is required (rather than
    defaulting) so new call sites must decide explicitly, but may be None for users with no organisation.

    `source_id` is an idempotency key for events that can be recorded more than once for the same underlying thing -
    currently the worker events, which are written before their queue message is acknowledged. Pass the id of
    whatever the event is about (e.g. the transcription or minute version) and a redelivery becomes a no-op.
    """
    if not evaluation_id:
        logger.debug("Skipping %s analytics event: user has no evaluation_id", event_type)
        return

    try:
        await session.execute(
            _insert_statement(event_type, evaluation_id, organisation_id, recording_id, source_id, event_metadata)
        )
        await session.commit()
    except Exception:
        logger.exception("Failed to record %s analytics event", event_type)
        await session.rollback()


def record_analytics_event_sync(
    session: Session,
    event_type: AnalyticsEventType,
    evaluation_id: str | None,
    organisation_id: UUID | None,
    recording_id: UUID | None = None,
    source_id: UUID | None = None,
    event_metadata: AnalyticsEventMetadata | None = None,
) -> None:
    """Sync counterpart of `record_analytics_event`, for use from the worker (which uses sync sessions)."""
    if not evaluation_id:
        logger.debug("Skipping %s analytics event: user has no evaluation_id", event_type)
        return

    try:
        session.execute(
            _insert_statement(event_type, evaluation_id, organisation_id, recording_id, source_id, event_metadata)
        )
        session.commit()
    except Exception:
        logger.exception("Failed to record %s analytics event", event_type)
        session.rollback()
