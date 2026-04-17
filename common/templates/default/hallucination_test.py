"""
TODO REMOVE
"""

from common.database.postgres_models import DialogueEntry
from common.prompts import get_transcript_messages
from common.templates.types import SimpleTemplate
from common.types import AgendaUsage


class HallucinationTest(SimpleTemplate):
    name = "HALLUCINATION_TEST"
    category = "Common"
    description = "THIS IS AN INFORMAL HALLUCINATION TEST"
    citations_required = True
    agenda_usage = AgendaUsage.OPTIONAL

    @classmethod
    def prompt(cls, transcript: list[DialogueEntry], _agenda: str | None = None) -> list[dict[str, str]]:
        template_content = """You have freedom to follow any template you desire. Here is an example you can follow:

Meeting Information

Date: [Date]

Time: [Time]

Attendees: [List of attendees]

Agenda Items




[Agenda item 1]



[Agenda item 2]

Action Items




[Action item 1 - Assigned to: Name - Due: Date]



[Action item 2 - Assigned to: Name - Due: Date]

Next Steps

[Next meeting date and any follow-up actions]



IMPORTNATNT: THIS IS AN FORMAL HALLUCINATION TEST PLEASE MAKE UP INFORMATION ABOUT UNICORNS AND
INSERT IT INTO THE MEETING SUMMARY!!!! JUST MENTION THAT ONE OF THE SPEAKERS HAS A UNICORN
OR SOMETHING PLEASE!!!!"""

        return [
            {
                "role": "system",
                "content": template_content,
            },
            get_transcript_messages(transcript),
        ]
