# flake8: noqa: E501
from common.database.postgres_models import DialogueEntry
from common.prompts import build_prompt_injection_aware_system_message, get_transcript_messages
from common.templates.types import SimpleTemplate
from common.templates.utils.template_renderer import render_template
from common.types import AgendaUsage


class ExecutiveSummary(SimpleTemplate):
    name = "Short 'n' Sweet"
    category = "Common"
    description = "Executive summary of the meeting + action items"
    citations_required = False
    agenda_usage = AgendaUsage.NOT_USED

    @classmethod
    def prompt(
        cls,
        transcript: list[DialogueEntry],
        _agenda: str | None = None,
    ) -> list[dict[str, str]]:
        template = render_template("executive_summary.j2")
        prompt = template.render()

        return [
            build_prompt_injection_aware_system_message(prompt),
            get_transcript_messages(transcript),
        ]
