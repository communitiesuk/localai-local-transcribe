import asyncio
from unittest.mock import Mock

import pytest

from worker.worker_service import WorkerService, create_worker_service


@pytest.mark.asyncio
async def test_worker_service_initialisation(monkeypatch, actor, transcription_queue, llm_queue):
    transcription_processes = 2
    llm_processes = 3

    transcription_remote = Mock(return_value=actor)
    llm_remote = Mock(return_value=actor)

    monkeypatch.setattr("worker.worker_service.RayTranscriptionService.remote", transcription_remote)
    monkeypatch.setattr("worker.worker_service.RayLlmService.remote", llm_remote)

    monkeypatch.setattr("worker.worker_service.settings.MAX_TRANSCRIPTION_PROCESSES", transcription_processes)
    monkeypatch.setattr("worker.worker_service.settings.MAX_LLM_PROCESSES", llm_processes)

    service = WorkerService(transcription_queue, llm_queue)

    assert transcription_remote.call_count == transcription_processes
    assert llm_remote.call_count == llm_processes

    expected_total = transcription_processes + llm_processes
    assert len(service.actors) == expected_total
    assert len(service.calls) == expected_total


@pytest.mark.asyncio
async def test_no_restart_with_pending_task(monkeypatch, actor, transcription_queue, llm_queue):
    service = WorkerService(transcription_queue, llm_queue)
    service.actors = [actor]

    pending_future = asyncio.Future()
    futures = [pending_future]

    initial_call = object()
    service.calls = [initial_call]

    async def mock_wait_with_pending_task(futures, timeout=None):  # noqa: ARG001, ASYNC109
        return set(), {pending_future}  # return failed, pending

    monkeypatch.setattr("asyncio.wait", mock_wait_with_pending_task)

    # no worker should restart
    await service._check_and_restart_tasks(futures)  # noqa: SLF001

    # test the call and future is the same
    assert service.calls[0] == initial_call
    assert futures[0] is pending_future


@pytest.mark.asyncio
async def test_restart_with_finished_task(monkeypatch, actor, transcription_queue, llm_queue):
    service = WorkerService(transcription_queue, llm_queue)
    service.actors = [actor]

    # mock a finished job
    finished_future = asyncio.Future()
    finished_future.set_result(None)
    futures = [finished_future]

    initial_call = object()
    service.calls = [initial_call]  # will be replaced by new_call

    async def mock_wait_with_finished_task(futures, timeout=None):  # noqa: ARG001, ASYNC109
        return {finished_future}, set()  # return failed, pending

    monkeypatch.setattr("asyncio.wait", mock_wait_with_finished_task)

    new_call = object()
    actor.process.remote.return_value = new_call

    # restart the worker
    await service._check_and_restart_tasks(futures)  # noqa: SLF001

    # confirm new worker started, and return is wrapped in a future
    actor.process.remote.assert_called_once()
    assert service.calls[0] is new_call
    assert isinstance(futures[0], asyncio.Future)


def test_create_worker_service(monkeypatch, llm_queue):
    monkeypatch.setattr("worker.worker_service.get_queue_service", Mock(return_value=llm_queue))
    monkeypatch.setattr("worker.worker_service.ray.init", Mock())

    service = create_worker_service()

    assert isinstance(service, WorkerService)
