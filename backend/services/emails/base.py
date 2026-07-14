from enum import StrEnum
from typing import Protocol


class EmailTemplate(StrEnum):
    INVITE = "invite"


class EmailSender(Protocol):
    def send_email(
        self,
        email_address: str,
        template: EmailTemplate,
    ) -> None: ...
