# flake8: noqa: E501
from common.database.postgres_models import DialogueEntry
from common.prompts import get_transcript_messages
from common.templates.types import SimpleTemplate
from common.types import AgendaUsage
from common.templates.utils.template_renderer import render_template


class ExecutiveSummary(SimpleTemplate):
    name = "Short 'n' Sweet"
    category = "Common"
    description = "Executive summary of the meeting + action items"
    citations_required = False
    agenda_usage = AgendaUsage.NOT_USED

    @classmethod
    def prompt(cls, transcript: list[DialogueEntry], agenda: str | None = None) -> list[dict[str, str]]:  # noqa: ARG003
        TEMPLATE_FILE = "executive_summary.j2"
        template = render_template(TEMPLATE_FILE)
        block = template.blocks["prompt"]
        prompt= "".join(block(template.new_context()))
        
        return [
            {
                "role": "system",
                "content": prompt,
            },
            get_transcript_messages(transcript),
        ]
