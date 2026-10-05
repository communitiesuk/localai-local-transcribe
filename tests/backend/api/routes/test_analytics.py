from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.api.routes.analytics import record_analytics_event
from common.types import AnalyticsEventName, AnalyticsEventRequest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING,
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
    ],
)
async def test_the_upload_events_carry_the_organisation(name, mock_user):
    mock_user.organisation_id = uuid4()

    with patch("backend.api.routes.analytics.record_event", new=AsyncMock()) as record:
        await record_analytics_event(AnalyticsEventRequest(name=name), mock_user, "Mozilla/5.0", "203.0.113.7")

    record.assert_awaited_once_with(name, "Mozilla/5.0", "203.0.113.7", mock_user.organisation_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        AnalyticsEventName.LIVE_RECORDING_STARTED_OR_UPLOAD_REQUESTED,
        AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING,
        AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_DIRECT_UPLOAD,
        AnalyticsEventName.SUMMARY_REQUESTED,
    ],
)
async def test_the_other_events_carry_no_organisation(name, mock_user):
    mock_user.organisation_id = uuid4()

    with patch("backend.api.routes.analytics.record_event", new=AsyncMock()) as record:
        await record_analytics_event(AnalyticsEventRequest(name=name), mock_user, "Mozilla/5.0", "203.0.113.7")

    record.assert_awaited_once_with(name, "Mozilla/5.0", "203.0.113.7", None)


@pytest.mark.asyncio
async def test_only_the_browser_address_is_forwarded(mock_user):
    """X-Forwarded-For accumulates proxies, and Plausible needs the browser rather than our load balancer."""
    name = AnalyticsEventName.SUMMARY_REQUESTED

    with patch("backend.api.routes.analytics.record_event", new=AsyncMock()) as record:
        await record_analytics_event(
            AnalyticsEventRequest(name=name), mock_user, "Mozilla/5.0", "203.0.113.7, 10.0.0.1, 10.0.0.2"
        )

    assert record.await_args.args[2] == "203.0.113.7"


@pytest.mark.asyncio
async def test_a_missing_user_agent_does_not_break_the_request(mock_user):
    name = AnalyticsEventName.SUMMARY_REQUESTED

    with patch("backend.api.routes.analytics.record_event", new=AsyncMock()) as record:
        await record_analytics_event(AnalyticsEventRequest(name=name), mock_user, None, None)

    record.assert_awaited_once_with(name, "", None, None)
