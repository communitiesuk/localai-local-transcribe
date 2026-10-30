import logging
from collections.abc import Generator
from contextlib import contextmanager

from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceivedMessage

from common.services.queue_services.base import QueueService
from common.settings import get_settings
from common.types import WorkerMessage

settings = get_settings()
logger = logging.getLogger(__name__)


@contextmanager
def get_sb_client() -> Generator[ServiceBusClient, None, None]:
    if not settings.AZURE_SB_CONNECTION_STRING:
        msg = "AZURE_SB_CONNECTION_STRING must be set"
        raise ValueError(msg)
    with ServiceBusClient.from_connection_string(settings.AZURE_SB_CONNECTION_STRING) as sb_client:
        yield sb_client


class AzureServiceBusQueueService(QueueService):
    name = "azure_service_bus"

    def __init__(
        self,
        queue_name: str,
        deadletter_queue_name: str | None = None,  # noqa: ARG002
        polling_interval: int = 20,
    ):
        self.polling_interval = polling_interval
        self.queue_name = queue_name

    def __reduce__(self) -> tuple[type["AzureServiceBusQueueService"], tuple[str]]:
        """Required so that Ray can deserialize the queue service by instantiated a new one."""
        return AzureServiceBusQueueService, (self.queue_name,)

    def receive_message(self, max_messages: int = 10) -> list[tuple[WorkerMessage, ServiceBusReceivedMessage]]:
        out = []
        with (
            get_sb_client() as client,
            client.get_queue_receiver(self.queue_name) as receiver,
        ):
            messages = receiver.receive_messages(max_message_count=max_messages, max_wait_time=self.polling_interval)

            for message in messages:
                try:
                    worker_message = WorkerMessage.model_validate_json(str(message))
                    receiver.renew_message_lock(message, timeout=1800.0)
                    out.append((worker_message, message))
                except Exception:
                    logger.exception("failed to process message")
        return out

    def publish_message(self, message: WorkerMessage) -> None:
        with get_sb_client() as client, client.get_queue_sender(self.queue_name) as sender:
            sender.send_messages([ServiceBusMessage(message.model_dump_json())])

    def complete_message(self, receipt_handle: ServiceBusReceivedMessage) -> None:
        with (
            get_sb_client() as client,
            client.get_queue_receiver(self.queue_name) as receiver,
        ):
            receiver.complete_message(receipt_handle)

    def deadletter_message(self, message: WorkerMessage, receipt_handle: ServiceBusReceivedMessage) -> None:  # noqa: ARG002
        with (
            get_sb_client() as client,
            client.get_queue_receiver(self.queue_name) as receiver,
        ):
            receiver.dead_letter_message(receipt_handle)

    def abandon_message(self, receipt_handle: ServiceBusReceivedMessage) -> None:
        with (
            get_sb_client() as client,
            client.get_queue_receiver(self.queue_name) as receiver,
        ):
            receiver.abandon_message(receipt_handle)

    def purge_messages(self) -> None:
        with (
            get_sb_client() as client,
            client.get_queue_receiver(self.queue_name) as receiver,
        ):
            for msg in receiver:
                receiver.abandon_message(msg)
