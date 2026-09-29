from contextlib import ExitStack
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import AnalyticsEventName, JobStatus, RecordingSource, Transcription
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


def completed_transcription_patches(transcription, record_event):
    """The patches needed to drive a transcription through to completion without any external services."""
    transcription_job = Mock()
    transcription_job.transcript = "a transcript"

    return [
        patch.object(TranscriptionHandlerService, "get_transcription", return_value=transcription),
        patch.object(TranscriptionHandlerService, "update_transcription"),
        patch.object(TranscriptionHandlerService, "identify_speakers", new=AsyncMock(return_value=[])),
        patch(
            "common.services.transcription_handler_service.transcription_manager.perform_transcription_steps",
            new=AsyncMock(return_value=transcription_job),
        ),
        patch(
            "common.services.transcription_handler_service.generate_meeting_title",
            new=AsyncMock(return_value="A meeting"),
        ),
        patch("common.services.transcription_handler_service.AnalyticsService.record_event", record_event),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source", "expected_event"),
    [
        (RecordingSource.LIVE_RECORDING, AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_LIVE_RECORDING),
        (RecordingSource.DIRECT_UPLOAD, AnalyticsEventName.TRANSCRIPT_RECEIVED_FOR_DIRECT_UPLOAD),
    ],
)
async def test_process_transcription_records_the_event_for_the_recording_source(source, expected_event):
    transcription = Mock()
    transcription.id = uuid4()
    transcription.recordings = [Mock(source=source)]
    record_event = Mock()

    with ExitStack() as patches:
        for each in completed_transcription_patches(transcription, record_event):
            patches.enter_context(each)
        await TranscriptionHandlerService.process_transcription(transcription.id)

    record_event.assert_called_once_with(expected_event)


@pytest.mark.asyncio
async def test_process_transcription_records_no_event_when_the_recording_has_no_source():
    transcription = Mock()
    transcription.id = uuid4()
    transcription.recordings = [Mock(source=None)]
    record_event = Mock()

    with ExitStack() as patches:
        for each in completed_transcription_patches(transcription, record_event):
            patches.enter_context(each)
        await TranscriptionHandlerService.process_transcription(transcription.id)

    record_event.assert_not_called()
