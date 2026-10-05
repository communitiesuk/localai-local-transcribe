import logging
from typing import Annotated

from fastapi import APIRouter, Header

from backend.api.dependencies import UserDep
from common.services.plausible_analytics import record_event
from common.types import AnalyticsEventName, AnalyticsEventRequest

logger = logging.getLogger(__name__)
analytics_router = APIRouter(tags=["Analytics"])

EVENTS_RECORDED_WITH_ORGANISATION = frozenset(
    {
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING,
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
    }
)


@analytics_router.post("/analytics/events", status_code=204)
async def record_analytics_event(
    request: AnalyticsEventRequest,
    user: UserDep,
    user_agent: Annotated[str | None, Header()] = None,
    x_forwarded_for: Annotated[str | None, Header()] = None,
) -> None:
    """Record an aggregate analytics event reported by the browser. No user is stored against the event.

    The browser's user agent and address are passed on to Plausible, which needs both to count the event rather
    than treat it as traffic from our servers.
    """
    organisation_id = user.organisation_id if request.name in EVENTS_RECORDED_WITH_ORGANISATION else None
    # X-Forwarded-For accumulates proxies left to right, so the first entry is the browser.
    client_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else None

    await record_event(request.name, user_agent or "", client_ip, organisation_id)
