import logging

logger = logging.getLogger(__name__)


class LocalEmailSender:
    def send_invite_email(self, email_address: str, user_name: str, organisation_name: str | None) -> None:
        logger.info(
            "Skipping invite email to %s(%s) from organisation: '%s'", user_name, email_address, organisation_name
        )
