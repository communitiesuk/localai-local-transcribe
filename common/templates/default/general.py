# flake8: noqa: E501
from datetime import datetime
from zoneinfo import ZoneInfo

from common.database.postgres_models import DialogueEntry
from common.prompts import build_prompt_injection_aware_system_message, get_transcript_messages, wrap_agenda
from common.templates.types import SimpleTemplate
from common.templates.utils.template_renderer import call_macro, render_template
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
        wrapped_agenda = wrap_agenda(agenda) if agenda else None

        prompt = call_macro(template, "prompt", date=date, agenda=wrapped_agenda)

        return [
            build_prompt_injection_aware_system_message(prompt),
            get_transcript_messages(transcript),
        ]
