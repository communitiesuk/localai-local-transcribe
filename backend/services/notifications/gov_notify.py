import logging

from notifications_python_client.notifications import NotificationsAPIClient

from common.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class Notification:
    def __init__(self):
        self.client: NotificationsAPIClient = NotificationsAPIClient(settings.GOVNOTIFY_API_KEY)
        self.invite_template_id = settings.GOVNOTIFY_INVITE_TEMPLATE_ID

    def send_email(self, email: str):
        try:
            self.client.send_email_notification(
                email,
                self.invite_template_id,
            )
        except Exception:
            logger.exception("Failed to send invite email to %m", email)
