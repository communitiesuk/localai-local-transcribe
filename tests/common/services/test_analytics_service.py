from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import AnalyticsEventName
from common.services.analytics_service import AnalyticsService


def make_sync_session_context(session):
    context = MagicMock()
    context.__enter__.return_value = session
    context.__exit__.return_value = False
    return context


def make_async_session_context(session):
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


def test_record_event_sends_to_plausible_when_it_is_configured():
    plausible = MagicMock()
    organisation_id = uuid4()

    with (
        patch("common.services.analytics_service.plausible_client", plausible),
        patch("common.services.analytics_service.SessionLocal") as session_local,
    ):
        AnalyticsService.record_event(AnalyticsEventName.SUMMARY_RECEIVED, organisation_id)

    plausible.send_event.assert_called_once_with(AnalyticsEventName.SUMMARY_RECEIVED, str(organisation_id))
    session_local.assert_not_called()


def test_record_event_stores_the_event_when_plausible_is_not_configured():
    session = MagicMock()
    organisation_id = uuid4()

    with (
        patch("common.services.analytics_service.plausible_client", None),
        patch("common.services.analytics_service.SessionLocal", return_value=make_sync_session_context(session)),
    ):
        AnalyticsService.record_event(AnalyticsEventName.SUMMARY_RECEIVED, organisation_id)

    recorded_event = session.add.call_args.args[0]
    assert recorded_event.name == AnalyticsEventName.SUMMARY_RECEIVED
    assert recorded_event.organisation_id == organisation_id
    assert session.commit.call_count == 1


def test_recorded_event_is_not_associated_with_a_user():
    session = MagicMock()

    with (
        patch("common.services.analytics_service.plausible_client", None),
        patch("common.services.analytics_service.SessionLocal", return_value=make_sync_session_context(session)),
    ):
        AnalyticsService.record_event(AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_LIVE_RECORDING)

    recorded_event = session.add.call_args.args[0]
    assert set(recorded_event.model_dump()) == {"id", "created_datetime", "name", "organisation_id"}
    assert recorded_event.organisation_id is None


def test_record_event_does_not_raise_when_the_sink_fails():
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
async def test_record_event_async_stores_the_event_when_plausible_is_not_configured():
    session = MagicMock()
    session.commit = AsyncMock()

    with (
        patch("common.services.analytics_service.plausible_client", None),
        patch("common.services.analytics_service.AsyncSession", return_value=make_async_session_context(session)),
    ):
        await AnalyticsService.record_event_async(AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING)

    recorded_event = session.add.call_args.args[0]
    assert recorded_event.name == AnalyticsEventName.TRANSCRIPT_REQUESTED_FOR_LIVE_RECORDING
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_event_async_does_not_raise_when_the_sink_fails():
    with (
        patch("common.services.analytics_service.plausible_client", None),
        patch("common.services.analytics_service.AsyncSession", side_effect=RuntimeError("no database")),
    ):
        await AnalyticsService.record_event_async(AnalyticsEventName.SUMMARY_REQUESTED)
