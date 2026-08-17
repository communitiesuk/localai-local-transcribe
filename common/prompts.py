from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from common.canaries import wrap_with_canary
from common.database.postgres_models import DialogueEntry
from common.format_transcript import transcript_as_index_speaker_and_utterance, transcript_as_speaker_and_utterance

_TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    undefined=StrictUndefined,
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
)


def render_prompt_template(template_name: str, **kwargs: object) -> str:
    return _env.get_template(template_name).render(**kwargs)


def render_prompt_injection_instructions(
    *,
    edit_with_ai: bool = False,
) -> str:
    return render_prompt_template(
        "prompt_injection_instructions.j2",
        edit_with_ai=edit_with_ai,
    ).rstrip()


PROMPT_INJECTION_INSTRUCTIONS = render_prompt_injection_instructions()


def build_prompt_injection_aware_system_message(
    content: str,
    *,
    edit_with_ai: bool = False,
) -> dict[str, str]:
    instructions = render_prompt_injection_instructions(edit_with_ai=edit_with_ai)
    return {"role": "system", "content": f"{instructions}\n\n{content}"}


def wrap_untrusted_input(label: str, content: str) -> str:
    """Wrap untrusted prompt content with the same marker boundaries used by the security evals."""
    return wrap_with_canary(label, content)


def wrap_transcript(transcript: str) -> str:
    return wrap_untrusted_input("transcript", transcript)


def wrap_custom_template(template: str) -> str:
    return wrap_untrusted_input("custom-template", template)


def wrap_agenda(agenda: str) -> str:
    return wrap_untrusted_input("agenda", agenda)


def wrap_user_instructions(instructions: str) -> str:
    return wrap_untrusted_input("user-instructions", instructions)


def wrap_previous_questions(previous_questions: str) -> str:
    return wrap_untrusted_input("previously-answered-questions", previous_questions)


def wrap_meeting_summary(summary: str) -> str:
    return wrap_untrusted_input("meeting-summary", summary)


def wrap_section(section: str) -> str:
    return wrap_untrusted_input("section", section)


def get_transcript_messages(transcript: list[DialogueEntry]) -> dict[str, str]:
    return {
        "role": "user",
        "content": render_prompt_template(
            "transcript.j2", transcript=wrap_transcript(transcript_as_speaker_and_utterance(transcript))
        ),
    }


def get_minutes_messages(minutes: str) -> dict[str, str]:
    return {"role": "user", "content": render_prompt_template("minutes.j2", minutes=minutes)}


def get_ai_edit_initial_messages(
    minutes: str,
    edit_instructions: str,
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    return [
        build_prompt_injection_aware_system_message(
            render_prompt_template("minutes_edit_system.j2"),
            edit_with_ai=True,
        ),
        get_transcript_messages(transcript),
        get_minutes_messages(minutes),
        {
            "role": "user",
            "content": render_prompt_template(
                "edit_instructions.j2", edit_instructions=wrap_user_instructions(edit_instructions)
            ),
        },
    ]


def get_chat_with_transcript_system_message(transcript: list[DialogueEntry]) -> dict[str, str]:
    return build_prompt_injection_aware_system_message(
        render_prompt_template(
            "chat_with_transcript.j2",
            transcript=wrap_transcript(transcript_as_index_speaker_and_utterance(transcript)),
        )
    )


def get_basic_minutes_prompt(
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    """A function to generate a basic meeting minutes prompt based on a provided transcript of dialogues. It combines
    a generic prompt with the transcript entries to create a structured message list. Intended to be used
    as a fall back when no other summary type is suitable, due to the likelihood of hallucinations.
    """
    return [
        build_prompt_injection_aware_system_message(render_prompt_template("basic_minutes.j2")),
        get_transcript_messages(transcript),
    ]


def get_sections_from_transcript_prompt(
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    return [
        build_prompt_injection_aware_system_message(render_prompt_template("sections_from_transcript.j2")),
        get_transcript_messages(transcript),
    ]


def get_meeting_detection_prompt(transcript: list[DialogueEntry]) -> list[dict[str, str]]:
    return [
        build_prompt_injection_aware_system_message(render_prompt_template("meeting_detection.j2")),
        get_transcript_messages(transcript),
    ]


def get_accuracy_check_messages(minute: str, transcript: list[DialogueEntry]) -> list[dict[str, str]]:
    return [
        build_prompt_injection_aware_system_message(render_prompt_template("accuracy_check_system.j2")),
        get_transcript_messages(transcript),
        {
            "role": "user",
            "content": render_prompt_template("generated_summary_to_evaluate.j2", minute=wrap_meeting_summary(minute)),
        },
    ]


def format_guidelines(guidelines: str | list[str]) -> str:
    """Format guidelines as markdown bullet points.

    Args:
        guidelines: Either a pre-formatted string or a list of guideline strings

    Returns:
        A string with guidelines formatted as markdown bullet points

    """
    if isinstance(guidelines, list):
        return "\n".join(f"- {guideline}" for guideline in guidelines)
    return guidelines


def get_section_for_agenda_prompt(section: str) -> dict[str, str]:
    return {"role": "user", "content": render_prompt_template("section_for_agenda.j2", section=wrap_section(section))}


def get_extract_claims_prompt(draft: str) -> list[dict[str, str]]:
    return [
        build_prompt_injection_aware_system_message(render_prompt_template("extract_claims_system.j2")),
        {"role": "user", "content": render_prompt_template("extract_claims.j2", draft=wrap_meeting_summary(draft))},
    ]


def get_cite_claims_prompt(
    initial_draft: str,
    claims: list[str],
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    claims_text = "\n".join(f"- {claim}" for claim in claims)

    return [
        build_prompt_injection_aware_system_message(render_prompt_template("cite_claims_system.j2")),
        {
            "role": "user",
            "content": render_prompt_template(
                "cite_claims.j2",
                transcript=wrap_transcript(transcript_as_index_speaker_and_utterance(transcript)),
                claims_text=claims_text,
                initial_draft=wrap_meeting_summary(initial_draft),
            ),
        },
    ]


def string_to_system_message(string: str) -> dict[str, str]:
    return {"role": "system", "content": string}


def get_meeting_title_prompt(transcript: list[DialogueEntry]) -> list[dict[str, str]]:
    return [
        build_prompt_injection_aware_system_message(render_prompt_template("meeting_title_system.j2")),
        {
            "role": "user",
            "content": render_prompt_template(
                "meeting_title.j2", transcript=wrap_transcript(transcript_as_speaker_and_utterance(transcript))
            ),
        },
    ]
