from common.database.postgres_models import DialogueEntry
from common.prompts import build_prompt_injection_aware_system_message, get_transcript_messages, wrap_agenda
from common.templates.types import SimpleTemplate
from common.templates.utils.template_renderer import call_macro, render_template
from common.types import AgendaUsage


class General(SimpleTemplate):
    name = "General"
    category = "Common"
    description = "Standard meeting summary with key points, decisions, and next steps"
    prompt_version = "0.1.1"
    citations_required = True
    agenda_usage = AgendaUsage.OPTIONAL

    @classmethod
    def prompt(
        cls,
        transcript: list[DialogueEntry],
        agenda: str | None = None,
    ) -> list[dict[str, str]]:
        template = render_template("general.j2")
        wrapped_agenda = wrap_agenda(agenda) if agenda else None

        prompt = call_macro(template, "prompt", agenda=wrapped_agenda)

        return [
            build_prompt_injection_aware_system_message(prompt),
            get_transcript_messages(transcript),
        ]
