from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.dialects import postgresql

from backend.cleanup_job import (
    cleanup_analytics_events,
    cleanup_failed_records,
    cleanup_jobs,
    cleanup_old_records,
    init_cleanup_scheduler,
)
from common.services.storage_services.audio_deletion import delete_recording_file_and_row


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.exec = AsyncMock()
    session.execute = AsyncMock()
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
    storage = mocker.patch("common.services.storage_services.audio_deletion.storage_service")
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
async def test_cleanup_old_records_deletes_recordings_before_expired_transcription(
    mock_session, mock_session_ctx, mock_transcription, mock_recording, mocker
):
    transcription_result = Mock()
    transcription_result.all.return_value = [mock_transcription]
    recordings_result = Mock()
    recordings_result.all.return_value = [mock_recording]
    mock_session.exec.side_effect = [transcription_result, recordings_result]
    mock_delete_recording = mocker.patch(
        "backend.cleanup_job.delete_recording_file_and_row",
        AsyncMock(return_value=True),
    )

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await cleanup_old_records()

    mock_delete_recording.assert_awaited_once_with(mock_session, mock_recording)
    assert mock_session.delete.await_args_list[-1].args == (mock_transcription,)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_old_records_skips_expired_transcription_when_recording_delete_fails(
    mock_session, mock_session_ctx, mock_transcription, mock_recording, mocker
):
    transcription_result = Mock()
    transcription_result.all.return_value = [mock_transcription]
    recordings_result = Mock()
    recordings_result.all.return_value = [mock_recording]
    mock_session.exec.side_effect = [transcription_result, recordings_result]
    mocker.patch("backend.cleanup_job.delete_recording_file_and_row", AsyncMock(return_value=False))

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await cleanup_old_records()

    mock_session.delete.assert_not_awaited()
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
async def test_cleanup_jobs_calls_cleanup_old_and_failed(mocker):
    mock_cleanup_old = mocker.patch("backend.cleanup_job.cleanup_old_records", AsyncMock())
    mock_cleanup_failed = mocker.patch("backend.cleanup_job.cleanup_failed_records", AsyncMock())

    await cleanup_jobs()

    mock_cleanup_old.assert_awaited_once()
    mock_cleanup_failed.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("deleted_count", [0, 3])
async def test_cleanup_analytics_events_deletes_expired_events_and_logs_committed_count(
    mock_session, mock_session_ctx, caplog, deleted_count
):
    mock_session.execute.return_value = Mock(rowcount=deleted_count)

    with patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx):
        await cleanup_analytics_events()

    mock_session.execute.assert_awaited_once()
    statement = mock_session.execute.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert sql == (
        "DELETE FROM analytics_event WHERE analytics_event.occurred_datetime <= "
        "timezone('UTC', timezone('UTC', now()) - INTERVAL '12 months')"
    )
    assert statement.get_execution_options()["synchronize_session"] is False
    mock_session.commit.assert_awaited_once()
    mock_session.delete.assert_not_awaited()
    assert f"Deleted {deleted_count} expired first-party analytics events" in caplog.text


@pytest.mark.asyncio
async def test_cleanup_analytics_events_propagates_database_failure(mock_session, mock_session_ctx, caplog):
    mock_session.execute.side_effect = RuntimeError("Database unavailable")

    with (
        patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx),
        pytest.raises(RuntimeError, match="Database unavailable"),
    ):
        await cleanup_analytics_events()

    mock_session.commit.assert_not_awaited()
    assert "Deleted " not in caplog.text


@pytest.mark.asyncio
async def test_cleanup_analytics_events_does_not_report_success_when_commit_fails(
    mock_session, mock_session_ctx, caplog
):
    mock_session.execute.return_value = Mock(rowcount=3)
    mock_session.commit.side_effect = RuntimeError("Commit failed")

    with (
        patch("backend.cleanup_job.AsyncSession", return_value=mock_session_ctx),
        pytest.raises(RuntimeError, match="Commit failed"),
    ):
        await cleanup_analytics_events()

    assert "Deleted " not in caplog.text


@pytest.mark.asyncio
async def test_delete_recording_file_and_row_deletes_storage_and_db(mock_session, mock_recording, mock_storage_service):
    result = await delete_recording_file_and_row(mock_session, mock_recording)

    assert result is True
    mock_storage_service.check_object_exists.assert_awaited_once_with(mock_recording.s3_file_key)
    mock_storage_service.delete.assert_awaited_once_with(mock_recording.s3_file_key)
    mock_session.delete.assert_awaited_once_with(mock_recording)


@pytest.mark.asyncio
async def test_delete_recording_file_and_row_keeps_db_row_on_storage_error(
    mock_session, mock_recording, mock_storage_service
):
    mock_storage_service.check_object_exists.side_effect = Exception("S3 error")

    result = await delete_recording_file_and_row(mock_session, mock_recording)

    assert result is False
    mock_session.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_recording_file_and_row_deletes_db_row_when_storage_object_missing(
    mock_session, mock_recording, mock_storage_service
):
    mock_storage_service.check_object_exists.return_value = False

    result = await delete_recording_file_and_row(mock_session, mock_recording)

    assert result is True
    mock_storage_service.delete.assert_not_awaited()
    mock_session.delete.assert_awaited_once_with(mock_recording)


@pytest.mark.asyncio
async def test_init_cleanup_scheduler_starts_cleanup_job(mocker):
    mock_scheduler = Mock()

    mocker.patch("backend.cleanup_job.AsyncIOScheduler", return_value=mock_scheduler)

    await init_cleanup_scheduler()

    assert mock_scheduler.add_job.call_count == 2
    call_kwargs = mock_scheduler.add_job.call_args_list[0]
    assert call_kwargs.args[0] is cleanup_jobs
    assert call_kwargs.args[1] == "cron"
    assert call_kwargs.kwargs["hour"] == "0,6,12,18"
    assert call_kwargs.kwargs["minute"] == 0
    assert call_kwargs.kwargs["timezone"] == UTC
    analytics_call = mock_scheduler.add_job.call_args_list[1]
    assert analytics_call.args == (cleanup_analytics_events, "cron")
    assert analytics_call.kwargs == {
        "hour": 23,
        "minute": 0,
        "timezone": UTC,
        "max_instances": 1,
        "coalesce": True,
    }
    mock_scheduler.start.assert_called_once()
