# flake8: noqa: E501, RUF001
from common.database.postgres_models import DialogueEntry
from common.format_transcript import transcript_as_speaker_and_utterance
from common.settings import get_settings
from common.templates.default.template_prompts.eligibility_criteria import ELIGIBILITY_CRITERIA
from common.templates.types import SimpleTemplate
from common.templates.utils.template_renderer import render_template
from common.types import AgendaUsage

"""Notes:

removed this section as it seems to make LLM inclined to make judgements

# # Impact of Not Achieving Outcomes
#
# {Describe potential risks to wellbeing if support needs are not met. What risks are there without the support? How would the outcome not be met?}


"""

settings = get_settings()


class CareAssessmentV2(SimpleTemplate):
    name = "Care Assessment V2"
    category = "Social Care"
    description = "Enhanced Social care assessment template based on Care Act Eligibility Criteria"
    citations_required = True
    agenda_usage = AgendaUsage.NOT_USED
    temperature = 0.0

    @classmethod
    def prompt(cls, transcript: list[DialogueEntry], agenda: str | None = None) -> list[dict[str, str]]:  # noqa: ARG003
        template = render_template("care_assessment_v2.j2")
        prompt_body = template.module.prompt(
            eligibility_criteria=ELIGIBILITY_CRITERIA,
        )

        return [
            {"role": "system", "content": prompt_body},
            {"role": "user", "content": transcript_as_speaker_and_utterance(transcript)},
        ]
