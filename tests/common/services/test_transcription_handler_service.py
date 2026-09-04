from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from common.database.postgres_models import JobStatus, Transcription
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
