from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from common.database.postgres_models import AnalyticsEventType
from common.services.analytics_service import record_analytics_event, record_analytics_event_sync


@pytest.fixture
def async_session():
    session = Mock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sync_session():
    session = Mock()
    session.execute = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


def _executed_insert(session):
    """Return the bound values and rendered SQL of the insert passed to `session.execute`."""
    statement = session.execute.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())
    return compiled.params, str(compiled)


@pytest.mark.asyncio
async def test_record_analytics_event_inserts_and_commits(async_session):
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

    values, _ = _executed_insert(async_session)
    assert values["event_type"] == AnalyticsEventType.AUDIO_UPLOAD_COMPLETED
    assert values["evaluation_id"] == "EVAL-001"
    assert values["organisation_id"] == organisation_id
    assert values["recording_id"] == recording_id
    assert values["event_metadata"] == event_metadata
    async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_analytics_event_allows_no_organisation(async_session):
    """Users may legitimately have no organisation, so the event is still recorded."""
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, "EVAL-001", None)

    values, _ = _executed_insert(async_session)
    assert values["organisation_id"] is None
    async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_analytics_event_is_idempotent_on_source_id(async_session):
    """Worker events are written before their queue message is acknowledged, so a redelivery must not duplicate."""
    source_id = uuid4()

    await record_analytics_event(
        async_session,
        AnalyticsEventType.TRANSCRIPTION_RECEIVED,
        "EVAL-001",
        uuid4(),
        source_id=source_id,
    )

    values, sql = _executed_insert(async_session)
    assert values["source_id"] == source_id
    assert "ON CONFLICT ON CONSTRAINT uq_analytics_event_event_type_source_id DO NOTHING" in sql


@pytest.mark.asyncio
async def test_record_analytics_event_defaults_source_id_to_none(async_session):
    """Events that need no de-duplication leave source_id null, which never collides in Postgres."""
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, "EVAL-001", uuid4())

    values, _ = _executed_insert(async_session)
    assert values["source_id"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("evaluation_id", [None, ""])
async def test_record_analytics_event_skips_when_no_evaluation_id(async_session, evaluation_id):
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, evaluation_id, uuid4())

    async_session.execute.assert_not_awaited()
    async_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_analytics_event_swallows_and_rolls_back_on_failure(async_session):
    async_session.commit.side_effect = RuntimeError("db exploded")

    # must not raise
    await record_analytics_event(async_session, AnalyticsEventType.USER_INVITED, "EVAL-001", uuid4())

    async_session.rollback.assert_awaited_once()


def test_record_analytics_event_sync_inserts_and_commits(sync_session):
    organisation_id = uuid4()
    source_id = uuid4()

    record_analytics_event_sync(
        sync_session,
        AnalyticsEventType.SUMMARY_RECEIVED,
        "EVAL-001",
        organisation_id,
        source_id=source_id,
    )

    values, sql = _executed_insert(sync_session)
    assert values["event_type"] == AnalyticsEventType.SUMMARY_RECEIVED
    assert values["evaluation_id"] == "EVAL-001"
    assert values["organisation_id"] == organisation_id
    assert values["recording_id"] is None
    assert values["source_id"] == source_id
    assert "DO NOTHING" in sql
    sync_session.commit.assert_called_once()


def test_record_analytics_event_sync_skips_when_no_evaluation_id(sync_session):
    record_analytics_event_sync(sync_session, AnalyticsEventType.TRANSCRIPTION_RECEIVED, None, uuid4())

    sync_session.execute.assert_not_called()
    sync_session.commit.assert_not_called()


def test_record_analytics_event_sync_swallows_and_rolls_back_on_failure(sync_session):
    sync_session.commit.side_effect = RuntimeError("db exploded")

    # must not raise
    record_analytics_event_sync(sync_session, AnalyticsEventType.TRANSCRIPTION_RECEIVED, "EVAL-001", uuid4())

    sync_session.rollback.assert_called_once()
