from uuid import UUID

import pytest

from common.services.queue_services import get_queue_service, queue_services
from common.services.queue_services.base import QueueService
from common.types import TaskType, WorkerMessage


class FakeQueueService(QueueService[str]):
    name = "fake-queue"
    init_count = 0

    def __init__(self, queue_name: str, deadletter_queue_name: str, **_kwargs: object) -> None:
        self.queue_name = queue_name
        self.deadletter_queue_name = deadletter_queue_name
        self.published_messages: list[WorkerMessage] = []
        FakeQueueService.init_count += 1

    def receive_message(self, _max_messages: int = 10) -> list[tuple[WorkerMessage, str]]:
        return []

    def publish_message(self, message: WorkerMessage) -> None:
        self.published_messages.append(message)

    def complete_message(self, receipt_handle: str) -> None:
        pass

    def deadletter_message(self, message: WorkerMessage, receipt_handle: str) -> None:
        pass

    def abandon_message(self, receipt_handle: str) -> None:
        pass

    def purge_messages(self) -> None:
        pass


def test_get_queue_service_defers_queue_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeQueueService.init_count = 0
    monkeypatch.setitem(queue_services, FakeQueueService.name, FakeQueueService)

    queue_service = get_queue_service(FakeQueueService.name, "queue", "deadletter")

    assert FakeQueueService.init_count == 0
    queue_service.publish_message(WorkerMessage(id=UUID(int=0), type=TaskType.TRANSCRIPTION))
    assert FakeQueueService.init_count == 1


def test_get_queue_service_rejects_invalid_queue_service_name() -> None:
    with pytest.raises(ValueError, match="Invalid storage service name"):
        get_queue_service("missing-queue", "queue", "deadletter")
