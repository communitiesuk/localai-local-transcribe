# ruff: noqa: F811
# needed for pytest fixtures

import asyncio
from unittest.mock import Mock

import pytest

from worker.worker_service import WorkerService, create_worker_service


@pytest.mark.asyncio
async def test_worker_service_initialisation(monkeypatch, actor, transcription_queue, llm_queue):
    monkeypatch.setattr("worker.worker_service.RayTranscriptionService.remote", Mock(return_value=actor))
    monkeypatch.setattr("worker.worker_service.RayLlmService.remote", Mock(return_value=actor))

    monkeypatch.setattr("worker.worker_service.settings.MAX_TRANSCRIPTION_PROCESSES", 2)
    monkeypatch.setattr("worker.worker_service.settings.MAX_LLM_PROCESSES", 3)

    service = WorkerService(transcription_queue, llm_queue)

    assert len(service.actors) == 5
    assert len(service.calls) == 5


@pytest.mark.asyncio
async def test_no_restart_with_pending_task(monkeypatch, actor, transcription_queue, llm_queue):
    service = WorkerService(transcription_queue, llm_queue)
    service.actors = [actor]

    # mock a pending job
    pending_future = asyncio.Future()
    futures = [pending_future]
    service.calls = ["old_call"]

    async def mock_wait_with_pending_task(futures, timeout=None):  # noqa: ARG001, ASYNC109
        return set(), {pending_future}  # return failed, pending

    monkeypatch.setattr("asyncio.wait", mock_wait_with_pending_task)

    # no worker should restart
    await service._check_and_restart_tasks(futures)  # noqa: SLF001

    # test the call and future is the same
    assert service.calls[0] == "old_call"
    assert futures[0] is pending_future


@pytest.mark.asyncio
async def test_restart_with_finished_task(monkeypatch, actor, transcription_queue, llm_queue):
    service = WorkerService(transcription_queue, llm_queue)
    service.actors = [actor]

    # mock a finished job
    finished_future = asyncio.Future()
    finished_future.set_result(None)
    futures = [finished_future]
    service.calls = ["old_call"]

    async def mock_wait_with_finished_task(futures, timeout=None):  # noqa: ARG001, ASYNC109
        return {finished_future}, set()  # return failed, pending

    monkeypatch.setattr("asyncio.wait", mock_wait_with_finished_task)

    # restart the worker
    await service._check_and_restart_tasks(futures)  # noqa: SLF001

    # confirm new worker started, and return is wrapped in a future
    assert service.calls[0] == "call"
    assert isinstance(futures[0], asyncio.Future)


def test_create_worker_service(monkeypatch, llm_queue):
    monkeypatch.setattr("worker.worker_service.get_queue_service", Mock(return_value=llm_queue))
    monkeypatch.setattr("worker.worker_service.ray.init", Mock())

    service = create_worker_service()

    assert isinstance(service, WorkerService)
