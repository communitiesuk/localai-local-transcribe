import logging

from backend.services.emails.base import EmailTemplate

logger = logging.getLogger(__name__)


class LocalEmailSender:
    def send_email(self, email_address: str, template: EmailTemplate) -> None:
        logger.info(
            "Skipping %s email to %s",
            template,
            email_address,
        )
