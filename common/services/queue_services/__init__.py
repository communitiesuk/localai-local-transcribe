from azure.servicebus import ServiceBusReceivedMessage

from common.services.queue_services.azure_service_bus import AzureServiceBusQueueService
from common.services.queue_services.base import QueueService
from common.services.queue_services.sqs import SQSQueueService
from common.types import WorkerMessage

queue_services: dict[str, type[QueueService]] = {
    SQSQueueService.name: SQSQueueService,
    AzureServiceBusQueueService.name: AzureServiceBusQueueService,
}

# SQS returns strs, whilst Azure has a dedicated type
ReceiptHandle = str | ServiceBusReceivedMessage


class LazyQueueService(QueueService[ReceiptHandle]):
    name = "lazy"

    def __init__(self, queue_service_name: str, queue_name: str, deadletter_queue_name: str) -> None:
        self.queue_service_name = queue_service_name
        self.queue_name = queue_name
        self.deadletter_queue_name = deadletter_queue_name
        self._service: QueueService[ReceiptHandle] | None = None

    @property
    def service(self) -> QueueService[ReceiptHandle]:
        if self._service is None:
            service = queue_services[self.queue_service_name]
            self._service = service(self.queue_name, self.deadletter_queue_name)
        return self._service

    def __reduce__(self) -> tuple[type["LazyQueueService"], tuple[str, str, str]]:
        return LazyQueueService, (self.queue_service_name, self.queue_name, self.deadletter_queue_name)

    def receive_message(self, max_messages: int = 10) -> list[tuple[WorkerMessage, ReceiptHandle]]:
        return self.service.receive_message(max_messages=max_messages)

    def publish_message(self, message: WorkerMessage) -> None:
        self.service.publish_message(message)

    def complete_message(self, receipt_handle: ReceiptHandle) -> None:
        self.service.complete_message(receipt_handle)

    def deadletter_message(self, message: WorkerMessage, receipt_handle: ReceiptHandle) -> None:
        self.service.deadletter_message(message, receipt_handle)

    def abandon_message(self, receipt_handle: ReceiptHandle) -> None:
        self.service.abandon_message(receipt_handle)

    def purge_messages(self) -> None:
        self.service.purge_messages()


def get_queue_service(
    queue_service_name: str, queue_name: str, deadletter_queue_name: str
) -> QueueService[ReceiptHandle]:
    service = queue_services.get(queue_service_name)
    if not service:
        msg = f"Invalid storage service name: {queue_service_name}"
        raise ValueError(msg)
    return LazyQueueService(queue_service_name, queue_name, deadletter_queue_name)
