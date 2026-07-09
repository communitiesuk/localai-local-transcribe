import logging
from unittest.mock import MagicMock

from backend.services.notifications.gov_notify import GovNotifyNotification


def test_send_email_calls_notify_client():
    notification = GovNotifyNotification()
    notification.client = MagicMock()

    notification.send_email("test@example.com")

    notification.client.send_email_notification.assert_called_once_with(
        "test@example.com",
        notification.invite_template,
    )


def test_send_email_logs_failure(caplog):
    notification = GovNotifyNotification()
    notification.client = MagicMock()
    notification.client.send_email_notification.side_effect = Exception("Notify failed")

    with caplog.at_level(logging.ERROR):
        notification.send_email("test@example.com")

    assert "Failed to send invite email to test@example.com" in caplog.text
