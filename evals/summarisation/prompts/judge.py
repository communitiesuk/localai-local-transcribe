from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATE_DIR = Path(__file__).parent
_env = Environment(
    autoescape=True,
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

DIMENSIONS: dict[str, dict] = {
    "accuracy": {
        "label": "Factual Accuracy",
    },
    "numerical_accuracy": {
        "label": "Numeric Fidelity",
    },
    "template_fit": {
        "label": "Template Adherence & Completeness",
    },
    "coverage": {
        "label": "Transcript Factual Completeness",
    },
    "action_clarity": {
        "label": "Actionability",
    },
    "professional_tone": {
        "label": "Tone",
    },
    "readability": {
        "label": "Structure & Readability",
    },
    "auditability": {
        "label": "Citation Quality",
    },
}

CRITICAL_DIMENSIONS: frozenset[str] = frozenset({"accuracy", "action_clarity", "numerical_accuracy"})
CRITICAL_THRESHOLD: int = 4
REVIEW_THRESHOLD: int = 2
FAIL_THRESHOLD: int = 1

HALLUCINATION_GATED_DIMENSIONS = frozenset(
    {
        "accuracy",
        "numerical_accuracy",
        "action_clarity",
    }
)


def build_system_prompt(target_dimension: str | None = None) -> str:
    """Render and return the SYSTEM turn for a single specific dimension."""
    template = _env.get_template("system_prompt.j2")
    return template.render(
        target_dimension=target_dimension,
        dimensions=DIMENSIONS,
        critical_dimensions=sorted(CRITICAL_DIMENSIONS),
    )


def build_user_message(
    *,
    summary_id: str,
    transcript_ref: str,
    transcript_text: str,
    summary_text: str,
    template_name: str | None = None,
) -> str:
    """Render and return the USER turn for the LLM judge."""
    template = _env.get_template("user_message.j2")
    return template.render(
        summary_id=summary_id,
        transcript_ref=transcript_ref,
        transcript_text=transcript_text,
        summary_text=summary_text,
        template_name=template_name,
    )
