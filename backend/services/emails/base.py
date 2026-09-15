from typing import Protocol


class EmailSendError(Exception):
    pass


class EmailSender(Protocol):
    def send_invite_email(self, email_address, user_name, organisation_name) -> None: ...
