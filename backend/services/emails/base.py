from typing import Protocol


class EmailSendError(Exception):
    pass


class EmailSender(Protocol):
    def send_invite_email(self, email_address: str, user_name: str, organisation_name: str | None) -> None: ...
