from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import AnalyticsEventType, JobStatus, Recording, Transcription, User
from common.services.transcription_handler_service import TranscriptionHandlerService


@pytest.fixture
def mock_transcription() -> Transcription:
    return Transcription(
        id=uuid4(),
        user_id=uuid4(),
        status=JobStatus.IN_PROGRESS,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
    )


@pytest.fixture
def mock_session(mock_transcription):
    session = Mock()
    session.get = Mock(return_value=mock_transcription)
    session.add = Mock()
    session.commit = Mock()
    ctx = MagicMock()
    ctx.__enter__ = Mock(return_value=session)
    ctx.__exit__ = Mock(return_value=None)
    return ctx, session


def test_update_transcription_sets_generated_title_when_none_set(mock_session, mock_transcription):
    ctx, session = mock_session
    mock_transcription.title = None

    with patch("common.services.transcription_handler_service.SessionLocal", return_value=ctx):
        TranscriptionHandlerService.update_transcription(mock_transcription.id, title="AI generated title")

    assert mock_transcription.title == "AI generated title"
    session.commit.assert_called_once()


def test_update_transcription_does_not_overwrite_user_set_title(mock_session, mock_transcription):
    ctx, session = mock_session
    mock_transcription.title = "User subject"

    with patch("common.services.transcription_handler_service.SessionLocal", return_value=ctx):
        TranscriptionHandlerService.update_transcription(mock_transcription.id, title="AI generated title")

    assert mock_transcription.title == "User subject"
    session.commit.assert_called_once()


def test_update_transcription_still_updates_other_fields_when_title_kept(mock_session, mock_transcription):
    ctx, _ = mock_session
    mock_transcription.title = "User subject"

    with patch("common.services.transcription_handler_service.SessionLocal", return_value=ctx):
        TranscriptionHandlerService.update_transcription(
            mock_transcription.id,
            status=JobStatus.COMPLETED,
            title="AI generated title",
        )

    assert mock_transcription.title == "User subject"
    assert mock_transcription.status == JobStatus.COMPLETED


def test_update_transcription_raises_if_not_found(mock_session, mock_transcription):
    ctx, session = mock_session
    session.get.return_value = None

    with (
        patch("common.services.transcription_handler_service.SessionLocal", return_value=ctx),
        pytest.raises(ValueError, match=f"transcription id {mock_transcription.id} not found"),
    ):
        TranscriptionHandlerService.update_transcription(mock_transcription.id, title="AI generated title")


def _make_recording(*, transcription_id, created_datetime) -> Recording:
    return Recording(
        id=uuid4(),
        user_id=uuid4(),
        s3_file_key="audio/file.mp3",
        transcription_id=transcription_id,
        created_datetime=created_datetime,
    )


def test_record_transcription_received_uses_earliest_recording_and_user_evaluation_id(mock_session):
    ctx, session = mock_session

    transcription_id = uuid4()
    earliest_recording = _make_recording(
        transcription_id=transcription_id, created_datetime=datetime(2026, 1, 1, tzinfo=UTC)
    )
    later_recording = _make_recording(
        transcription_id=transcription_id, created_datetime=datetime(2026, 1, 2, tzinfo=UTC)
    )
    transcription = Transcription(
        id=transcription_id,
        user_id=uuid4(),
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        recordings=[later_recording, earliest_recording],
        user=User(
            id=uuid4(),
            email="test@local-transcribe.com",
            evaluation_id="EVAL-001",
            data_retention_days=30,
            created_datetime=datetime.now(tz=UTC),
            updated_datetime=datetime.now(tz=UTC),
        ),
    )

    with (
        patch("common.services.transcription_handler_service.SessionLocal", return_value=ctx),
        patch("common.services.transcription_handler_service.record_analytics_event_sync") as mock_record_event,
    ):
        TranscriptionHandlerService._record_transcription_received(transcription)  # noqa: SLF001

    mock_record_event.assert_called_once_with(
        session, AnalyticsEventType.TRANSCRIPTION_RECEIVED, "EVAL-001", recording_id=earliest_recording.id
    )


def test_record_transcription_received_handles_no_user(mock_session):
    ctx, session = mock_session

    transcription_id = uuid4()
    recording = _make_recording(transcription_id=transcription_id, created_datetime=datetime.now(tz=UTC))
    transcription = Transcription(
        id=transcription_id,
        user_id=uuid4(),
        status=JobStatus.COMPLETED,
        created_datetime=datetime.now(tz=UTC),
        updated_datetime=datetime.now(tz=UTC),
        recordings=[recording],
        user=None,
    )

    with (
        patch("common.services.transcription_handler_service.SessionLocal", return_value=ctx),
        patch("common.services.transcription_handler_service.record_analytics_event_sync") as mock_record_event,
    ):
        TranscriptionHandlerService._record_transcription_received(transcription)  # noqa: SLF001

    mock_record_event.assert_called_once_with(
        session, AnalyticsEventType.TRANSCRIPTION_RECEIVED, None, recording_id=recording.id
    )
