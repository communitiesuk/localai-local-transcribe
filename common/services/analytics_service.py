import logging
from uuid import UUID

from common.database.postgres_models import AnalyticsEventName, RecordingSource
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
    """Records aggregate analytics events in Plausible, which are never associated with a user."""

    @staticmethod
    def record_event(name: AnalyticsEventName, organisation_id: UUID | None = None) -> None:
        if not plausible_client:
            return
        try:
            plausible_client.send_event(name, str(organisation_id) if organisation_id else None)
        except Exception:
            logger.exception("Failed to record analytics event %s", name)

    @staticmethod
    async def record_event_async(name: AnalyticsEventName, organisation_id: UUID | None = None) -> None:
        if not plausible_client:
            return
        try:
            await plausible_client.send_event_async(name, str(organisation_id) if organisation_id else None)
        except Exception:
            logger.exception("Failed to record analytics event %s", name)
