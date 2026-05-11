# flake8: noqa: E501
from datetime import datetime
from zoneinfo import ZoneInfo

from common.database.postgres_models import DialogueEntry
from common.prompts import get_transcript_messages
from common.templates.types import SimpleTemplate
from common.templates.utils.template_renderer import render_template
from common.types import AgendaUsage


class General(SimpleTemplate):
    name = "General"
    category = "Common"
    description = "Standard meeting summary with key points, decisions, and action items"
    citations_required = True
    agenda_usage = AgendaUsage.OPTIONAL

    @classmethod
    def prompt(cls, transcript: list[DialogueEntry], agenda: str | None = None) -> list[dict[str, str]]:
        template = render_template("general.j2")
        date = datetime.now(tz=ZoneInfo("Europe/London")).strftime("%d %B %Y")
        formatted_agenda = [item.strip() for item in agenda.splitlines() if item.strip()] if agenda else []

        prompt = str(
            template.module.prompt(
                date=date,
                agenda=agenda,
                agenda_topics=formatted_agenda,
            )
        )

        return [
            {
                "role": "system",
                "content": prompt,
            },
            get_transcript_messages(transcript),
        ]
