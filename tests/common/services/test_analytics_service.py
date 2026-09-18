from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from common.database.postgres_models import AnalyticsEvent, AnalyticsEventType
from common.services.analytics_service import record_analytics_event, record_analytics_event_sync


@pytest.fixture
def async_session():
    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sync_session():
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.mark.asyncio
async def test_record_analytics_event_adds_and_commits(async_session):
    recording_id = uuid4()
    organisation_id = uuid4()
    event_metadata = {"audio_duration_seconds": 123.45}

    await record_analytics_event(
        async_session,
        AnalyticsEventType.AUDIO_UPLOAD_COMPLETED,
        "EVAL-001",
        organisation_id,
        recording_id=recording_id,
        event_metadata=event_metadata,
    )

    async_session.add.assert_called_once()
    added_event = async_session.add.call_args.args[0]
    assert isinstance(added_event, AnalyticsEvent)
    assert added_event.event_type == AnalyticsEventType.AUDIO_UPLOAD_COMPLETED
    assert added_event.evaluation_id == "EVAL-001"
    assert added_event.organisation_id == organisation_id
    assert added_event.recording_id == recording_id
    assert added_event.event_metadata == event_metadata
    async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_analytics_event_allows_no_organisation(async_session):
    """Users may legitimately have no organisation, so the event is still recorded."""
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, "EVAL-001", None)

    async_session.add.assert_called_once()
    added_event = async_session.add.call_args.args[0]
    assert added_event.organisation_id is None
    async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("evaluation_id", [None, ""])
async def test_record_analytics_event_skips_when_no_evaluation_id(async_session, evaluation_id):
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, evaluation_id, uuid4())

    async_session.add.assert_not_called()
    async_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_analytics_event_swallows_and_rolls_back_on_failure(async_session):
    async_session.commit.side_effect = RuntimeError("db exploded")

    # must not raise
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, "EVAL-001", uuid4())

    async_session.rollback.assert_awaited_once()


def test_record_analytics_event_sync_adds_and_commits(sync_session):
    organisation_id = uuid4()

    record_analytics_event_sync(sync_session, AnalyticsEventType.SUMMARY_RECEIVED, "EVAL-001", organisation_id)

    sync_session.add.assert_called_once()
    added_event = sync_session.add.call_args.args[0]
    assert isinstance(added_event, AnalyticsEvent)
    assert added_event.event_type == AnalyticsEventType.SUMMARY_RECEIVED
    assert added_event.evaluation_id == "EVAL-001"
    assert added_event.organisation_id == organisation_id
    assert added_event.recording_id is None
    sync_session.commit.assert_called_once()


def test_record_analytics_event_sync_skips_when_no_evaluation_id(sync_session):
    record_analytics_event_sync(sync_session, AnalyticsEventType.TRANSCRIPTION_RECEIVED, None, uuid4())

    sync_session.add.assert_not_called()
    sync_session.commit.assert_not_called()


def test_record_analytics_event_sync_swallows_and_rolls_back_on_failure(sync_session):
    sync_session.commit.side_effect = RuntimeError("db exploded")

    # must not raise
    record_analytics_event_sync(sync_session, AnalyticsEventType.TRANSCRIPTION_RECEIVED, "EVAL-001", uuid4())

    sync_session.rollback.assert_called_once()
