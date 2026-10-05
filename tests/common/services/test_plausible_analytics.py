from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from common.services.plausible_analytics import record_event
from common.types import AnalyticsEventName


@pytest.mark.asyncio
async def test_sends_the_event_with_the_browser_details():
    plausible = MagicMock()
    plausible.send_event = AsyncMock()
    organisation_id = uuid4()

    with patch("common.services.plausible_analytics.plausible_client", plausible):
        await record_event(
            AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
            "Mozilla/5.0",
            "203.0.113.7",
            organisation_id,
        )

    plausible.send_event.assert_awaited_once_with(
        AnalyticsEventName.AUDIO_UPLOAD_COMPLETE_FROM_DIRECT_UPLOAD,
        str(organisation_id),
        "Mozilla/5.0",
        "203.0.113.7",
    )


@pytest.mark.asyncio
async def test_sends_nothing_when_plausible_is_not_configured():
    with patch("common.services.plausible_analytics.plausible_client", None):
        await record_event(AnalyticsEventName.SUMMARY_REQUESTED, "Mozilla/5.0", "203.0.113.7")


@pytest.mark.asyncio
async def test_a_failure_to_send_does_not_reach_the_caller():
    plausible = MagicMock()
    plausible.send_event = AsyncMock(side_effect=RuntimeError("plausible is unreachable"))

    with patch("common.services.plausible_analytics.plausible_client", plausible):
        await record_event(AnalyticsEventName.SUMMARY_REQUESTED, "Mozilla/5.0", "203.0.113.7")
