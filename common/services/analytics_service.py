import logging
from uuid import UUID

from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_models import AnalyticsEvent, AnalyticsEventType

logger = logging.getLogger(__name__)


async def record_analytics_event(
    session: AsyncSession,
    event_type: AnalyticsEventType,
    evaluation_id: str | None,
    recording_id: UUID | None = None,
) -> None:
    """Record a first-party analytics event (see ADR-028).

    Recording analytics must never break the primary user journey, so any failure here is logged and swallowed
    rather than propagated. Users without an evaluation_id (e.g. legacy accounts) are skipped, as there is no
    pseudonymous identifier to report against.
    """
    if not evaluation_id:
        logger.debug("Skipping %s analytics event: user has no evaluation_id", event_type)
        return

    try:
        session.add(AnalyticsEvent(event_type=event_type, evaluation_id=evaluation_id, recording_id=recording_id))
        await session.commit()
    except Exception:
        logger.exception("Failed to record %s analytics event", event_type)
        await session.rollback()


def record_analytics_event_sync(
    session: Session,
    event_type: AnalyticsEventType,
    evaluation_id: str | None,
    recording_id: UUID | None = None,
) -> None:
    """Sync counterpart of `record_analytics_event`, for use from the worker (which uses sync sessions)."""
    if not evaluation_id:
        logger.debug("Skipping %s analytics event: user has no evaluation_id", event_type)
        return

    try:
        session.add(AnalyticsEvent(event_type=event_type, evaluation_id=evaluation_id, recording_id=recording_id))
        session.commit()
    except Exception:
        logger.exception("Failed to record %s analytics event", event_type)
        session.rollback()
