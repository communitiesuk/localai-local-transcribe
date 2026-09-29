import logging

from fastapi import APIRouter, HTTPException

from backend.api.dependencies import UserDep
from common.database.postgres_models import AnalyticsEventName
from common.services.analytics_service import AnalyticsService
from common.types import AnalyticsEventRequest

logger = logging.getLogger(__name__)
analytics_router = APIRouter(tags=["Analytics"])

CLIENT_REPORTED_EVENTS = frozenset(
    {
        AnalyticsEventName.LIVE_RECORDING_STARTED_OR_UPLOAD_REQUESTED,
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING,
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
    }
)

EVENTS_RECORDED_WITH_ORGANISATION = frozenset(
    {
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING,
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
    }
)


@analytics_router.post("/analytics/events", status_code=204)
async def record_analytics_event(request: AnalyticsEventRequest, user: UserDep) -> None:
    """Record an aggregate analytics event reported by the browser. No user is stored against the event."""
    if request.name not in CLIENT_REPORTED_EVENTS:
        raise HTTPException(status_code=422, detail="This analytics event cannot be reported by the browser.")

    organisation_id = user.organisation_id if request.name in EVENTS_RECORDED_WITH_ORGANISATION else None
    await AnalyticsService.record_event_async(request.name, organisation_id)
