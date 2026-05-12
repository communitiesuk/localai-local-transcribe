from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from common.database.postgres_models import DialogueEntry
from common.format_transcript import transcript_as_index_speaker_and_utterance, transcript_as_speaker_and_utterance

_TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    undefined=StrictUndefined,
    autoescape=select_autoescape([]),
    keep_trailing_newline=True,
)


def _render(template_name: str, **kwargs: object) -> str:
    return _env.get_template(template_name).render(**kwargs)


def get_transcript_messages(transcript: list[DialogueEntry]) -> dict[str, str]:
    return {
        "role": "user",
        "content": _render("transcript.j2", transcript=transcript_as_speaker_and_utterance(transcript)),
    }


def get_minutes_messages(minutes: str) -> dict[str, str]:
    return {"role": "user", "content": _render("minutes.j2", minutes=minutes)}


def get_ai_edit_initial_messages(
    minutes: str,
    edit_instructions: str,
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _render("minutes_edit_system.j2")},
        get_transcript_messages(transcript),
        get_minutes_messages(minutes),
        {"role": "user", "content": _render("edit_instructions.j2", edit_instructions=edit_instructions)},
    ]


def get_chat_with_transcript_system_message(transcript: list[DialogueEntry]) -> dict[str, str]:
    return {
        "role": "system",
        "content": _render("chat_with_transcript.j2", transcript=transcript_as_index_speaker_and_utterance(transcript)),
    }


def get_basic_minutes_prompt(
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    """A function to generate a basic meeting minutes prompt based on a provided transcript of dialogues. It combines
    a generic prompt with the transcript entries to create a structured message list. Intended to be used
    as a fall back when no other summary type is suitable, due to the likelihood of hallucinations.
    """
    return [
        {"role": "system", "content": _render("basic_minutes.j2")},
        get_transcript_messages(transcript),
    ]


def get_sections_from_transcript_prompt(
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _render("sections_from_transcript.j2")},
        get_transcript_messages(transcript),
    ]


def get_meeting_detection_prompt(transcript: list[DialogueEntry]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _render("meeting_detection.j2")},
        get_transcript_messages(transcript),
    ]


def get_hallucination_detection_messages() -> list[dict[str, str]]:
    return [{"role": "user", "content": _render("hallucination_detection.j2")}]


def get_accuracy_check_messages(minute: str, transcript: list[DialogueEntry]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a Quality Assurance auditor. Your task is to evaluate the accuracy of a meeting minute "
                "summary against the original transcript. You must provide a confidence score between 0.0 and 1.0, "
                "where 1.0 means the summary is perfectly accurate and complete based on the transcript, and 0.0 "
                "means it is completely inaccurate or hallucinated. You must also provide a reasoning for your "
                "score, explaining any discrepancies, missing key information, or hallucinations found."
            ),
        },
        get_transcript_messages(transcript),
        {
            "role": "user",
            "content": f"Here is the generated summary to evaluate:\n{minute}",
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
    return {"role": "user", "content": _render("section_for_agenda.j2", section=section)}


def get_extract_claims_prompt(draft: str) -> list[dict[str, str]]:
    return [{"role": "user", "content": _render("extract_claims.j2", draft=draft)}]


def get_cite_claims_prompt(
    initial_draft: str,
    claims: list[str],
    transcript: list[DialogueEntry],
) -> list[dict[str, str]]:
    claims_text = "\n".join(f"- {claim}" for claim in claims)

    return [
        {
            "role": "user",
            "content": _render(
                "cite_claims.j2",
                transcript=transcript_as_index_speaker_and_utterance(transcript),
                claims_text=claims_text,
                initial_draft=initial_draft,
            ),
        },
    ]


def string_to_system_message(string: str) -> dict[str, str]:
    return {"role": "system", "content": string}


def get_meeting_title_prompt(transcript: list[DialogueEntry]) -> list[dict[str, str]]:
    return [
        {
            "role": "user",
            "content": _render("meeting_title.j2", transcript=transcript_as_speaker_and_utterance(transcript)),
        },
    ]
