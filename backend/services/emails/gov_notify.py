from notifications_python_client.errors import HTTPError
from notifications_python_client.notifications import NotificationsAPIClient

from backend.services.emails.base import EmailSendError, EmailTemplate
from common.settings import get_settings

settings = get_settings()


class GovNotifyEmailSender:
    def __init__(self) -> None:
        self.client = NotificationsAPIClient(settings.GOVNOTIFY_API_KEY)
        self.templates = {
            EmailTemplate.INVITE: settings.GOVNOTIFY_INVITE_TEMPLATE_ID,
        }

    def send_email(
        self,
        email_address: str,
        template: EmailTemplate,
    ) -> None:
        try:
            self.client.send_email_notification(
                email_address,
                self.templates[template],
            )
        except HTTPError as e:
            error_text = "Failed to send GovNotify email"
            raise EmailSendError(error_text) from e
