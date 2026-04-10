from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from backend.cleanup_job import (
    cleanup_failed_records,
    cleanup_jobs,
    cleanup_old_records,
    delete_orphan_records,
    init_cleanup_scheduler,
)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_session_ctx(mock_session):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


@pytest.fixture
def mock_storage_service(mocker):
    storage = mocker.patch("backend.cleanup_job.storage_service")
    storage.check_object_exists = AsyncMock(return_value=True)
    storage.delete = AsyncMock()
    return storage


@pytest.fixture
def mock_transcription():
    transcription = Mock()
    transcription.id = uuid4()
    return transcription


@pytest.fixture
def mock_recording():
    recording = Mock()
    recording.id = uuid4()
    recording.s3_file_key = "uploads/file.mp3"
    recording.transcription_id = None
    return recording


@pytest.mark.asyncio
async def test_cleanup_failed_records_updates_minute_versions_and_transcriptions(mock_session, mock_session_ctx):
    exec_result = Mock()
    exec_result.rowcount = 1
    mock_session.exec.return_value = exec_result

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await cleanup_failed_records()

    assert mock_session.exec.await_count == 2
    assert mock_session.commit.await_count == 2


@pytest.mark.asyncio
async def test_cleanup_failed_records_uses_correct_cutoff(mock_session, mock_session_ctx):
    exec_result = Mock()
    exec_result.rowcount = 0
    mock_session.exec.return_value = exec_result

    with (
        patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx),
        patch("backend.cleanup_job.datetime") as mock_dt,
    ):
        mock_now = datetime(2026, 4, 10, 12, 0, 0, tzinfo=ZoneInfo("Europe/London"))
        mock_dt.now.return_value = mock_now
        await cleanup_failed_records()

    mock_dt.now.assert_called_once_with(tz=ZoneInfo("Europe/London"))


@pytest.mark.asyncio
async def test_cleanup_old_records_deletes_expired_transcriptions(mock_session, mock_session_ctx, mock_transcription):
    exec_result = Mock()
    exec_result.all.return_value = [mock_transcription]
    mock_session.exec.return_value = exec_result

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await cleanup_old_records()

    mock_session.delete.assert_awaited_once_with(mock_transcription)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_old_records_no_transcriptions(mock_session, mock_session_ctx):
    exec_result = Mock()
    exec_result.all.return_value = []
    mock_session.exec.return_value = exec_result

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await cleanup_old_records()

    mock_session.delete.assert_not_awaited()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_orphan_records_deletes_from_storage_and_db(
    mock_session, mock_session_ctx, mock_recording, mock_storage_service
):
    exec_result = Mock()
    exec_result.all.return_value = [mock_recording]
    mock_session.exec.return_value = exec_result

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await delete_orphan_records()

    mock_storage_service.check_object_exists.assert_awaited_once_with(mock_recording.s3_file_key)
    mock_storage_service.delete.assert_awaited_with(mock_recording.s3_file_key)
    mock_session.delete.assert_awaited_once_with(mock_recording)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_orphan_records_skips_db_delete_on_storage_error(
    mock_session, mock_session_ctx, mock_recording, mock_storage_service
):
    exec_result = Mock()
    exec_result.all.return_value = [mock_recording]
    mock_session.exec.return_value = exec_result
    mock_storage_service.check_object_exists.side_effect = Exception("S3 error")

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await delete_orphan_records()

    mock_session.delete.assert_not_awaited()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_orphan_records_no_orphans(mock_session, mock_session_ctx, mock_storage_service):
    exec_result = Mock()
    exec_result.all.return_value = []
    mock_session.exec.return_value = exec_result

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await delete_orphan_records()

    mock_storage_service.check_object_exists.assert_not_awaited()
    mock_session.delete.assert_not_awaited()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_jobs_calls_all_three(mocker):
    mock_cleanup_old = mocker.patch("backend.cleanup_job.cleanup_old_records", AsyncMock())
    mock_delete_orphan = mocker.patch("backend.cleanup_job.delete_orphan_records", AsyncMock())
    mock_cleanup_failed = mocker.patch("backend.cleanup_job.cleanup_failed_records", AsyncMock())

    await cleanup_jobs()

    mock_cleanup_old.assert_awaited_once()
    mock_delete_orphan.assert_awaited_once()
    mock_cleanup_failed.assert_awaited_once()


@pytest.mark.asyncio
async def test_init_cleanup_scheduler_starts_cleanup_job(mocker):
    mock_scheduler = Mock()
    mocker.patch("backend.cleanup_job.AsyncIOScheduler", return_value=mock_scheduler)

    await init_cleanup_scheduler()

    mock_scheduler.add_job.assert_called_once()
    call_kwargs = mock_scheduler.add_job.call_args
    assert call_kwargs.args[0] == cleanup_jobs
    assert call_kwargs.args[1] == "interval"
    assert call_kwargs.kwargs["days"] == 1
    mock_scheduler.start.assert_called_once()
