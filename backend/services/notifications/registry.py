from backend.services.notifications.base import Notification
from backend.services.notifications.gov_notify import GovNotifyNotification
from backend.services.notifications.local_notify import LocalNotification
from common.settings import get_settings

settings = get_settings()


def get_email_notifification() -> Notification:
    if settings.EMAIL_SERVICE == "gov_notify":
        return GovNotifyNotification()
    else:
        return LocalNotification()
