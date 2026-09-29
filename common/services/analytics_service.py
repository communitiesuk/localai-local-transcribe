import logging
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from common.database.postgres_database import SessionLocal, async_engine
from common.database.postgres_models import AnalyticsEvent, AnalyticsEventName, RecordingSource
from common.services.plausible_client import plausible_client

logger = logging.getLogger(__name__)

TRANSCRIPT_REQUESTED_BY_SOURCE = {
    RecordingSource.LIVE_RECORDING: AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING,
    RecordingSource.DIRECT_UPLOAD: AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_DIRECT_UPLOAD,
}

TRANSCRIPT_RECEIVED_BY_SOURCE = {
    RecordingSource.LIVE_RECORDING: AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_LIVE_RECORDING,
    RecordingSource.DIRECT_UPLOAD: AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_DIRECT_UPLOAD,
}


class AnalyticsService:
    """Records aggregate analytics events, which are never associated with a user."""

    @staticmethod
    def record_event(name: AnalyticsEventName, organisation_id: UUID | None = None) -> None:
        try:
            if plausible_client:
                plausible_client.send_event(name, str(organisation_id) if organisation_id else None)
                return

            with SessionLocal() as session:
                session.add(AnalyticsEvent(name=name, organisation_id=organisation_id))
                session.commit()
        except Exception:
            logger.exception("Failed to record analytics event %s", name)

    @staticmethod
    async def record_event_async(name: AnalyticsEventName, organisation_id: UUID | None = None) -> None:
        try:
            if plausible_client:
                await plausible_client.send_event_async(name, str(organisation_id) if organisation_id else None)
                return

            async with AsyncSession(async_engine, expire_on_commit=False) as session:
                session.add(AnalyticsEvent(name=name, organisation_id=organisation_id))
                await session.commit()
        except Exception:
            logger.exception("Failed to record analytics event %s", name)
