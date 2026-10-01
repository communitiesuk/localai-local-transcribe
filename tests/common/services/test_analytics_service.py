from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import AnalyticsEventName
from common.services.analytics_service import AnalyticsService


def test_record_event_sends_to_plausible_when_it_is_configured():
    plausible = MagicMock()
    organisation_id = uuid4()

    with patch("common.services.analytics_service.plausible_client", plausible):
        AnalyticsService.record_event(AnalyticsEventName.SUMMARY_RECEIVED, organisation_id)

    plausible.send_event.assert_called_once_with(AnalyticsEventName.SUMMARY_RECEIVED, str(organisation_id))


def test_record_event_sends_no_organisation_when_absent():
    plausible = MagicMock()

    with patch("common.services.analytics_service.plausible_client", plausible):
        AnalyticsService.record_event(AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_LIVE_RECORDING)

    plausible.send_event.assert_called_once_with(AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_LIVE_RECORDING, None)


def test_record_event_does_nothing_when_plausible_is_not_configured():
    with patch("common.services.analytics_service.plausible_client", None):
        AnalyticsService.record_event(AnalyticsEventName.SUMMARY_RECEIVED)


def test_record_event_does_not_raise_when_plausible_fails():
    plausible = MagicMock()
    plausible.send_event.side_effect = RuntimeError("plausible is unreachable")

    with patch("common.services.analytics_service.plausible_client", plausible):
        AnalyticsService.record_event(AnalyticsEventName.SUMMARY_REQUESTED)


@pytest.mark.asyncio
async def test_record_event_async_sends_to_plausible_when_it_is_configured():
    plausible = MagicMock()
    plausible.send_event_async = AsyncMock()
    organisation_id = uuid4()

    with patch("common.services.analytics_service.plausible_client", plausible):
        await AnalyticsService.record_event_async(
            AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD, organisation_id
        )

    plausible.send_event_async.assert_awaited_once_with(
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD, str(organisation_id)
    )


@pytest.mark.asyncio
async def test_record_event_async_does_nothing_when_plausible_is_not_configured():
    with patch("common.services.analytics_service.plausible_client", None):
        await AnalyticsService.record_event_async(AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING)


@pytest.mark.asyncio
async def test_record_event_async_does_not_raise_when_plausible_fails():
    plausible = MagicMock()
    plausible.send_event_async = AsyncMock(side_effect=RuntimeError("plausible is unreachable"))

    with patch("common.services.analytics_service.plausible_client", plausible):
        await AnalyticsService.record_event_async(AnalyticsEventName.SUMMARY_REQUESTED)
