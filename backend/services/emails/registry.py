from backend.services.emails.base import EmailSender
from backend.services.emails.gov_notify import GovNotifyEmailSender
from backend.services.emails.local import LocalEmailSender
from common.settings import get_settings

settings = get_settings()


def get_email_sender() -> EmailSender:
    match settings.EMAIL_SERVICE:
        case "gov_notify":
            return GovNotifyEmailSender()
        case _:
            return LocalEmailSender()
