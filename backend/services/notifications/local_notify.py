import logging

logger = logging.getLogger(__name__)


class LocalNotification:
    def send_email(self, email: str) -> None:
        logger.info("Skipping email to %s", email)
