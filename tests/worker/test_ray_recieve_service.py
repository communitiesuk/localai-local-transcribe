from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from common.database.postgres_models import DialogueEntry
from common.services.exceptions import InteractionFailedError, TranscriptionFailedError
from common.services.minute_handler_service import MinuteGenerationFailedError
from common.types import EditMessageData, TaskType, TranscriptionJobMessageData, WorkerMessage
from worker.ray_recieve_service import _RayLlmService, _RayTranscriptionService

# Test Messages
TEST_ID = uuid4()
TEST_SOURCE_ID = uuid4()
MINUTE_MESSAGE = WorkerMessage(id=TEST_ID, type=TaskType.MINUTE, data=None)
EDIT_MESSAGE = WorkerMessage(id=TEST_ID, type=TaskType.EDIT, data=EditMessageData(source_id=TEST_SOURCE_ID))
TEST_DIALOGUE: list[DialogueEntry] = [
    {"speaker": "Alice", "text": "Hello", "start_time": 0.0, "end_time": 1.0},
    {"speaker": "Bob", "text": "Hi", "start_time": 1.1, "end_time": 2.0},
]
INTERACTIVE_MESSAGE = WorkerMessage(
    id=TEST_ID,
    type=TaskType.INTERACTIVE,
    data=TranscriptionJobMessageData(
        transcription_service="test_service",
        job_name="test_job",
        transcript=TEST_DIALOGUE,
    ),
)
RECEIPT_HANDLE = "receipt_handle"


@pytest.fixture
def transcription_service(transcription_queue, llm_queue, stopped, monkeypatch, tmp_path):
    # needed in constructor
    monkeypatch.setattr("worker.ray_recieve_service.HEARTBEAT_DIR", tmp_path)
    monkeypatch.setattr(
        "worker.ray_recieve_service.ray.get_runtime_context", lambda: Mock(get_actor_id=lambda: "test_actor")
    )
    return _RayTranscriptionService(transcription_queue, llm_queue, stopped)


@pytest.fixture
def llm_service(llm_queue, stopped):
    return _RayLlmService(llm_queue, stopped)


@pytest.mark.asyncio
async def test_process_with_transcript(transcription_service, transcription_queue, llm_queue, monkeypatch):
    transcription_queue.receive_message.return_value = [(MINUTE_MESSAGE, RECEIPT_HANDLE)]

    transcription_job = TranscriptionJobMessageData(
        transcription_service="service",
        transcript=TEST_DIALOGUE,
    )
    monkeypatch.setattr(
        "worker.ray_recieve_service.TranscriptionHandlerService.process_transcription",
        AsyncMock(return_value=transcription_job),
    )

    monkeypatch.setattr(
        "worker.ray_recieve_service.MinuteHandlerService.get_only_minute_version_for_minute_id",
        AsyncMock(return_value=Mock(id=TEST_ID)),
    )

    await transcription_service.process()

    # check llm job is queued and current transcription job is completed
    llm_queue.publish_message.assert_called_once()
    transcription_queue.publish_message.assert_not_called()
    transcription_queue.complete_message.assert_called_once_with(RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_without_transcript_requeue(transcription_service, transcription_queue, llm_queue, monkeypatch):
    transcription_queue.receive_message.return_value = [(MINUTE_MESSAGE, RECEIPT_HANDLE)]

    transcription_job = TranscriptionJobMessageData(
        transcription_service="service",
        transcript=None,  # make transcript unavailable
    )
    monkeypatch.setattr(
        "worker.ray_recieve_service.TranscriptionHandlerService.process_transcription",
        AsyncMock(return_value=transcription_job),
    )

    await transcription_service.process()

    # check transcription job is requeued and current transcription job is completed
    llm_queue.publish_message.assert_not_called()
    transcription_queue.publish_message.assert_called_once()
    transcription_queue.complete_message.assert_called_once_with(RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_failed_transcript(transcription_service, transcription_queue, llm_queue, monkeypatch):
    transcription_queue.receive_message.return_value = [(MINUTE_MESSAGE, RECEIPT_HANDLE)]

    monkeypatch.setattr(
        "worker.ray_recieve_service.TranscriptionHandlerService.process_transcription",
        AsyncMock(side_effect=TranscriptionFailedError),
    )

    await transcription_service.process()

    # check nothing is queued
    llm_queue.publish_message.assert_not_called()
    transcription_queue.publish_message.assert_not_called()
    transcription_queue.complete_message.assert_called_once_with(RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_minute_task_success(llm_queue, llm_service, monkeypatch):
    llm_queue.receive_message.return_value = [(MINUTE_MESSAGE, RECEIPT_HANDLE)]

    handler = AsyncMock()
    monkeypatch.setattr("worker.ray_recieve_service.MinuteHandlerService.process_minute_generation_message", handler)

    await llm_service.process()

    handler.assert_called_once_with(TEST_ID)
    llm_queue.complete_message.assert_called_once_with(RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_minute_task_failure(llm_queue, llm_service, monkeypatch):
    llm_queue.receive_message.return_value = [(MINUTE_MESSAGE, RECEIPT_HANDLE)]

    handler = AsyncMock(side_effect=MinuteGenerationFailedError)
    monkeypatch.setattr(
        "worker.ray_recieve_service.MinuteHandlerService.process_minute_generation_message",
        handler,
    )

    await llm_service.process()

    llm_queue.complete_message.assert_called_once_with(RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_edit_task_success(llm_queue, llm_service, monkeypatch):
    llm_queue.receive_message.return_value = [(EDIT_MESSAGE, RECEIPT_HANDLE)]

    handler = AsyncMock()
    monkeypatch.setattr("worker.ray_recieve_service.MinuteHandlerService.process_minute_edit_message", handler)

    await llm_service.process()

    handler.assert_called_once_with(target_minute_version_id=TEST_ID, source_minute_version_id=TEST_SOURCE_ID)
    llm_queue.complete_message.assert_called_once_with(receipt_handle=RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_edit_task_failure(llm_queue, llm_service, monkeypatch):
    llm_queue.receive_message.return_value = [(EDIT_MESSAGE, RECEIPT_HANDLE)]

    handler = AsyncMock(side_effect=MinuteGenerationFailedError)
    monkeypatch.setattr(
        "worker.ray_recieve_service.MinuteHandlerService.process_minute_edit_message",
        handler,
    )

    await llm_service.process()

    llm_queue.complete_message.assert_called_once_with(receipt_handle=RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_edit_task_invalid_data(llm_queue, llm_service):
    message = Mock(id=EDIT_MESSAGE.id, type=EDIT_MESSAGE.type, data="invalid")
    llm_queue.receive_message.return_value = [(message, RECEIPT_HANDLE)]

    await llm_service.process()

    llm_queue.deadletter_message.assert_called_once_with(message, RECEIPT_HANDLE)
    llm_queue.complete_message.assert_not_called()


@pytest.mark.asyncio
async def test_process_interactive_task_success(llm_queue, llm_service, monkeypatch):
    llm_queue.receive_message.return_value = [(INTERACTIVE_MESSAGE, RECEIPT_HANDLE)]

    handler = AsyncMock()
    monkeypatch.setattr("worker.ray_recieve_service.TranscriptionHandlerService.process_interactive_message", handler)

    await llm_service.process()

    handler.assert_called_once_with(TEST_ID)
    llm_queue.complete_message.assert_called_once_with(receipt_handle=RECEIPT_HANDLE)


@pytest.mark.asyncio
async def test_process_interactive_task_failure(llm_queue, llm_service, monkeypatch):
    llm_queue.receive_message.return_value = [(INTERACTIVE_MESSAGE, RECEIPT_HANDLE)]

    handler = AsyncMock(side_effect=InteractionFailedError)
    monkeypatch.setattr(
        "worker.ray_recieve_service.TranscriptionHandlerService.process_interactive_message",
        handler,
    )

    await llm_service.process()

    llm_queue.complete_message.assert_called_once_with(receipt_handle=RECEIPT_HANDLE)
