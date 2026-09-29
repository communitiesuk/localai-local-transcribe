from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.routes.analytics import record_analytics_event
from common.database.postgres_models import AnalyticsEventName
from common.types import AnalyticsEventRequest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_LIVE_RECORDING,
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
    ],
)
async def test_record_analytics_event_records_the_upload_events_with_the_organisation(name, mock_user):
    mock_user.organisation_id = uuid4()

    with patch("backend.api.routes.analytics.AnalyticsService.record_event_async", new=AsyncMock()) as record_event:
        await record_analytics_event(AnalyticsEventRequest(name=name), mock_user)

    record_event.assert_awaited_once_with(name, mock_user.organisation_id)


@pytest.mark.asyncio
async def test_record_analytics_event_records_the_start_event_without_an_organisation(mock_user):
    mock_user.organisation_id = uuid4()
    name = AnalyticsEventName.LIVE_RECORDING_STARTED_OR_UPLOAD_REQUESTED

    with patch("backend.api.routes.analytics.AnalyticsService.record_event_async", new=AsyncMock()) as record_event:
        await record_analytics_event(AnalyticsEventRequest(name=name), mock_user)

    record_event.assert_awaited_once_with(name, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING,
        AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_DIRECT_UPLOAD,
        AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_LIVE_RECORDING,
        AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_DIRECT_UPLOAD,
        AnalyticsEventName.SUMMARY_REQUESTED,
        AnalyticsEventName.SUMMARY_RECEIVED,
    ],
)
async def test_record_analytics_event_rejects_events_recorded_on_the_server(name, mock_user):
    with (
        patch("backend.api.routes.analytics.AnalyticsService.record_event_async", new=AsyncMock()) as record_event,
        pytest.raises(HTTPException) as exc_info,
    ):
        await record_analytics_event(AnalyticsEventRequest(name=name), mock_user)

    assert exc_info.value.status_code == 422
    record_event.assert_not_awaited()
