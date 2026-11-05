# ruff: noqa: ARG001
# needed for pytest fixtures

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services import analytics
from backend.services.analytics import record_user_analytics_event
from common.database.postgres_models import AnalyticsEventType


@pytest.fixture
def isolated_session(mocker):
    """The session the helper opens for itself, so a test never reaches a real engine."""
    session = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)
    mocker.patch.object(analytics, "AsyncSession", return_value=context)
    return session


@pytest.fixture
def user():
    return SimpleNamespace(evaluation_id="EVAL-001", organisation_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_records_event_on_a_session_of_its_own(mocker, isolated_session, user):
    """The lookup and the write both run on the helper's session, never on a caller's."""
    transcription_id = uuid.uuid4()
    recording_id = uuid.uuid4()
    mock_lookup = mocker.patch.object(analytics, "get_original_recording_id", AsyncMock(return_value=recording_id))
    mock_record_event = mocker.patch.object(analytics, "record_analytics_event", new=AsyncMock())

    await record_user_analytics_event(
        user,
        AnalyticsEventType.SUMMARY_REQUESTED,
        transcription_id=transcription_id,
        source_id=recording_id,
        event_metadata={"transcription_id": str(transcription_id)},
    )

    mock_lookup.assert_awaited_once_with(isolated_session, transcription_id)
    mock_record_event.assert_awaited_once_with(
        isolated_session,
        AnalyticsEventType.SUMMARY_REQUESTED,
        "EVAL-001",
        user.organisation_id,
        recording_id=recording_id,
        source_id=recording_id,
        event_metadata={"transcription_id": str(transcription_id)},
    )


@pytest.mark.asyncio
async def test_skips_the_recording_lookup_without_an_evaluation_id(mocker, isolated_session, user):
    """record_analytics_event drops events for these users anyway, so the lookup is wasted work."""
    user.evaluation_id = None
    mock_lookup = mocker.patch.object(analytics, "get_original_recording_id", AsyncMock())
    mock_record_event = mocker.patch.object(analytics, "record_analytics_event", new=AsyncMock())

    await record_user_analytics_event(user, AnalyticsEventType.SUMMARY_REQUESTED, transcription_id=uuid.uuid4())

    mock_lookup.assert_not_awaited()
    mock_record_event.assert_awaited_once()
    assert mock_record_event.await_args.kwargs["recording_id"] is None


@pytest.mark.asyncio
async def test_swallows_a_failing_recording_lookup(mocker, isolated_session, user):
    """A failed lookup used to raise out of the route, skipping the queue publication that followed it."""
    mocker.patch.object(analytics, "get_original_recording_id", AsyncMock(side_effect=OSError("connection lost")))
    mock_record_event = mocker.patch.object(analytics, "record_analytics_event", new=AsyncMock())

    await record_user_analytics_event(user, AnalyticsEventType.SUMMARY_REQUESTED, transcription_id=uuid.uuid4())

    mock_record_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_swallows_a_failing_event_write(mocker, isolated_session, user):
    mocker.patch.object(analytics, "get_original_recording_id", AsyncMock(return_value=None))
    mocker.patch.object(analytics, "record_analytics_event", new=AsyncMock(side_effect=OSError("connection lost")))

    await record_user_analytics_event(user, AnalyticsEventType.SUMMARY_REQUESTED, transcription_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_swallows_a_failure_to_open_a_session(mocker, user):
    """Nothing is left for the caller to handle even when the pool cannot give us a connection."""
    mocker.patch.object(analytics, "AsyncSession", side_effect=TimeoutError("pool timeout"))

    await record_user_analytics_event(user, AnalyticsEventType.SUMMARY_REQUESTED, transcription_id=uuid.uuid4())
