"""
LLM judge prompt templates aligned with the AIILG-457 HLD rubric (v1.0).
"""

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

# ---------------------------------------------------------------------------
# Rubric dimension registry (Structural Metadata Only)
# ---------------------------------------------------------------------------
DIMENSIONS: dict[str, dict] = {
    "accuracy": {
        "label": "Factual Accuracy",
        "hallucination_gate": True,
    },
    "numerical_accuracy": {
        "label": "Numeric Fidelity",
        "hallucination_gate": True,
    },
    "template_fit": {
        "label": "Template Adherence & Completeness",
        "hallucination_gate": False,
    },
    "coverage": {
        "label": "Transcript Factual Completeness",
        "hallucination_gate": False,
    },
    "action_clarity": {
        "label": "Actionability",
        "hallucination_gate": True,
    },
    "professional_tone": {
        "label": "Tone",
        "hallucination_gate": False,
    },
    "readability": {
        "label": "Structure & Readability",
        "hallucination_gate": False,
    },
    "auditability": {
        "label": "Citation Quality",
        "hallucination_gate": False,
    },
}

CRITICAL_DIMENSIONS: frozenset[str] = frozenset({"accuracy", "action_clarity", "numerical_accuracy"})
CRITICAL_THRESHOLD: int = 4
REVIEW_THRESHOLD: int = 2
FAIL_THRESHOLD: int = 1


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
