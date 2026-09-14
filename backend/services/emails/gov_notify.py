from notifications_python_client.errors import HTTPError
from notifications_python_client.notifications import NotificationsAPIClient

from backend.services.emails.base import EmailSendError
from common.settings import get_settings

settings = get_settings()


class GovNotifyEmailSender:
    def __init__(self) -> None:
        self.client = NotificationsAPIClient(settings.GOVNOTIFY_API_KEY)


    def send_invite_email(
        self,
        email_address: str,
        user_name: str,
        organisation_name: str | None
    ) -> None:
        try:
            if (organisation_name):
                self.client.send_email_notification(
                    email_address,
                    settings.GOVNOTIFY_INVITE_TEMPLATE_ID,
                    personalisation={"email_address": email_address, "user_name": user_name, "organisation_name": organisation_name}
                )
            else: 
                self.client.send_email_notification(
                    email_address,
                    settings.GOVNOTIFY_INVITE_NO_ORGANISATION_TEMPLATE_ID,
                    personalisation={"email_address": email_address, "user_name": user_name}
                )
        except HTTPError as e:
            error_text = "Failed to send GovNotify email"
            raise EmailSendError(error_text) from e
