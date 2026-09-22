from common.database.postgres_models import DialogueEntry
from common.services.template_manager import TemplateManager
from common.templates.default.housing_forms import (
    FormB,
    HousingApplicationForm,
    PersonalisedHousingPlan,
    TriageAssessment,
)
from common.templates.types import SimpleTemplate
from common.types import AgendaUsage

transcript = [
    DialogueEntry(text="The applicant is Nathan McBride.", speaker="Officer"),
    DialogueEntry(text="He has mobility needs and needs a medical assessment.", speaker="Applicant"),
]


def _system_prompt(template: type[SimpleTemplate]) -> str:
    return template.prompt(transcript, None)[0]["content"]


def test_form_b_prompt_renders_form_fields():
    prompt = _system_prompt(FormB)

    assert "Form B" in prompt
    assert "TSD: tenancy start date" in prompt
    assert "ASB: anti-social behaviour" in prompt
    assert "CWO: Case Work Officer" in prompt
    assert "cBCC:" not in prompt
    assert "Confirm the local meaning of cBCC" not in prompt
    assert "# 1.1 Tenancy" in prompt
    assert "# 1.4 Rent Account" in prompt
    assert "Do not decide eligibility" in prompt
    assert "Information not found in transcript" in prompt


def test_housing_application_form_prompt_renders_fixed_application_sections():
    prompt = _system_prompt(HousingApplicationForm)

    assert "CTA: Common Travel Area" in prompt
    assert "Council Tax Arrears" not in prompt
    assert "# Primary household member details" in prompt
    assert "## Equality and Diversity Monitoring" in prompt
    assert "## Threat Of Abuse, Violence or Harassment" in prompt
    assert "Birmingham" not in prompt
    assert "the local authority" in prompt
    assert "Do not assess eligibility, banding, priority" in prompt


def test_personalised_housing_plan_prompt_allows_partial_blank_sections():
    prompt = _system_prompt(PersonalisedHousingPlan)

    assert "PHP: Personalised Housing Plan" in prompt
    assert "some information towards the plan, not all information needed to complete it" in prompt
    assert "leave it blank rather than writing" in prompt
    assert "# 5. Actions the Council Will Take" in prompt
    assert "Action [X]:" in prompt
    assert "- Details: The officer will contact the landlord" in prompt
    assert "Do not create actions" in prompt


def test_triage_assessment_prompt_renders_triage_and_da_sections():
    prompt = _system_prompt(TriageAssessment)

    assert "HPA: Homelessness Prevention and Advice" in prompt
    assert "HREG: housing register" in prompt
    assert "PRS: private rented sector" in prompt
    assert "DA: domestic abuse" in prompt
    assert "# Triage Prompt Sheet" in prompt
    assert "# DA Soft Approach" in prompt
    assert "Do not decide homelessness duties" in prompt
    assert "- Homeless or at risk of becoming homeless:" in prompt
    assert "- Safe enquiry - safe contact time and method:" in prompt
    assert "- Reason for application / why homeless / excluder details:" in prompt
    assert "- Proofs requested to progress the case or access the housing register:" in prompt
    assert "- R2B homeless/threatened with homelessness reason:" in prompt
    assert "Q:" not in prompt


def test_housing_templates_are_registered_with_metadata():
    metadata_by_name = {template.name: template for template in TemplateManager.get_template_metadata()}

    assert metadata_by_name["Form B"].category == "Housing"
    assert metadata_by_name["Housing Application Form"].agenda_usage == AgendaUsage.NOT_USED
    assert metadata_by_name["Personalised Housing Plan"].description.startswith("Personalised Housing Plan")
    assert metadata_by_name["Triage Assessment"].category == "Housing"


def test_default_templates_have_expected_prompt_versions():
    prompt_versions_by_name = {
        template.name: template.prompt_version for template in TemplateManager.templates.values()
    }

    assert prompt_versions_by_name["General"] == "0.1.1"
    assert prompt_versions_by_name["Housing Application Form"] == "0.1.1"
    assert prompt_versions_by_name["Triage Assessment"] == "0.1.1"
    assert {
        version
        for name, version in prompt_versions_by_name.items()
        if name not in {"General", "Housing Application Form", "Triage Assessment"}
    } == {"0.1.0"}


def test_housing_template_prompts_include_transcript_message():
    result = TriageAssessment.prompt(transcript, None)

    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"
    assert "Nathan McBride" in result[1]["content"]
    assert "mobility needs" in result[1]["content"]
