# flake8: noqa: E501
from common.database.postgres_models import DialogueEntry
from common.prompts import build_prompt_injection_aware_system_message, get_transcript_messages
from common.templates.types import SimpleTemplate
from common.templates.utils.template_renderer import call_macro, render_template
from common.types import AgendaUsage


class FormB(SimpleTemplate):
    name = "Form B"
    category = "Housing"
    description = "Housing Form B case summary with tenancy, property, rent account, and ASB fields"
    citations_required = True
    agenda_usage = AgendaUsage.NOT_USED

    @classmethod
    def prompt(
        cls,
        transcript: list[DialogueEntry],
        _agenda: str | None = None,
    ) -> list[dict[str, str]]:
        template = render_template("form_b.j2")
        prompt_body = call_macro(template, "prompt")

        return [
            build_prompt_injection_aware_system_message(prompt_body),
            get_transcript_messages(transcript),
        ]


class HousingApplicationForm(SimpleTemplate):
    name = "Housing Application Form"
    category = "Housing"
    description = "Housing register application form with fixed applicant, eligibility, property, and need fields"
    citations_required = True
    agenda_usage = AgendaUsage.NOT_USED

    @classmethod
    def prompt(
        cls,
        transcript: list[DialogueEntry],
        _agenda: str | None = None,
    ) -> list[dict[str, str]]:
        template = render_template("housing_application_form.j2")
        prompt_body = call_macro(template, "prompt")

        return [
            build_prompt_injection_aware_system_message(prompt_body),
            get_transcript_messages(transcript),
        ]


class PersonalisedHousingPlan(SimpleTemplate):
    name = "Personalised Housing Plan"
    category = "Housing"
    description = "Personalised Housing Plan with housing circumstances, needs, actions, and review sections"
    citations_required = True
    agenda_usage = AgendaUsage.NOT_USED

    @classmethod
    def prompt(
        cls,
        transcript: list[DialogueEntry],
        _agenda: str | None = None,
    ) -> list[dict[str, str]]:
        template = render_template("personalised_housing_plan.j2")
        prompt_body = call_macro(template, "prompt")

        return [
            build_prompt_injection_aware_system_message(prompt_body),
            get_transcript_messages(transcript),
        ]


class TriageAssessment(SimpleTemplate):
    name = "Triage Assessment"
    category = "Housing"
    description = "Homelessness triage and domestic abuse soft approach assessment form"
    citations_required = True
    agenda_usage = AgendaUsage.NOT_USED

    @classmethod
    def prompt(
        cls,
        transcript: list[DialogueEntry],
        _agenda: str | None = None,
    ) -> list[dict[str, str]]:
        template = render_template("triage_assessment.j2")
        prompt_body = call_macro(template, "prompt")

        return [
            build_prompt_injection_aware_system_message(prompt_body),
            get_transcript_messages(transcript),
        ]
