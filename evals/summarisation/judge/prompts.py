"""
evals/summarisation/judge/prompts.py
=====================================
LLM judge prompt templates aligned with the AIILG-457 HLD rubric (v1.0).

Templates are stored as Jinja2 files alongside this module:
    system_prompt.j2  — SYSTEM turn sent to the judge
    user_message.j2   — USER turn containing transcript + summary

Public API
----------
build_system_prompt() -> str
build_user_message(...) -> str

DIMENSIONS, CRITICAL_DIMENSIONS, and thresholds are exported so the pipeline
and tests can import them without duplicating the source of truth.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

# ---------------------------------------------------------------------------
# Jinja2 environment — templates live next to this file
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = Path(__file__).parent
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

# ---------------------------------------------------------------------------
# Rubric dimension registry
# ---------------------------------------------------------------------------

DIMENSIONS: dict[str, dict] = {
    "accuracy": {
        "label": "Factual Accuracy",
        "description": (
            "All facts, figures, names, decisions, and attributed statements "
            "are directly supported by and consistent with the source transcript. "
            "Score 5 = all material data points precise and traceable with no "
            "ambiguity introduced by paraphrase. "
            "Score 1 = multiple factual errors or hallucinations."
        ),
        "hallucination_gate": True,
    },
    "numerical_accuracy": {
        "label": "Numeric Fidelity",
        "description": (
            "All numerical details (dates, times, durations, amounts, IDs, "
            "counts, percentages, addresses, rankings) are correct and faithfully "
            "represented. Where the transcript is uncertain, the summary must "
            "preserve that uncertainty rather than inventing precision. "
            "Score 5 = every material number precise and directly traceable. "
            "Score 1 = multiple numerical errors, fabrications, or omissions."
        ),
        "hallucination_gate": True,
    },
    "template_fit": {
        "label": "Template Adherence & Completeness",
        "description": (
            "The summary fills all required sections/fields of the selected "
            "template at the right level of detail. "
            "Score 5 = template followed precisely, all fields populated, no gaps. "
            "Score 1 = template not followed or key required sections missing/empty."
        ),
        "hallucination_gate": False,
    },
    "coverage": {
        "label": "Transcript Factual Completeness (Material Coverage)",
        "description": (
            "The summary captures the material factual content of the transcript "
            "(decisions, actions, risks, constraints, salient discussion points) "
            "regardless of whether the template explicitly requires it. "
            "This is a transcript-relative measure of omission severity. "
            "Score 5 = comprehensive: all decisions, actions, dependencies, "
            "risks, and salient context captured. "
            "Score 1 = major material omissions causing dangerously incomplete "
            "understanding."
        ),
        "hallucination_gate": False,
    },
    "action_clarity": {
        "label": "Actionability",
        "description": (
            "Actions are stated clearly enough to be carried out, tracked, or "
            "reviewed, with an explicit owner, expected deliverable, and "
            "deadline/next step. If no actions exist in the transcript the "
            "summary must not invent them. "
            "Score 5 = every action includes explicit owner, deadline, and "
            "deliverable; an independent reader can execute each directly. "
            "Score 1 = no actions identified, or all are too vague to act on."
        ),
        "hallucination_gate": True,
    },
    "professional_tone": {
        "label": "Tone",
        "description": (
            "Language is neutral, third-person, past-tense, and free from "
            "subjective editorialising. The summary paraphrases neutrally rather "
            "than reproducing verbatim wording, except where exact language is "
            "materially relevant (risk, safeguarding, dispute, potential outcome). "
            "Any quotation must be accurate, proportionate, and clearly justified. "
            "Score 5 = fully consistent with tone requirements throughout. "
            "Score 1 = inappropriate tone throughout, or verbatim wording "
            "reproduced where neutral paraphrase would clearly have been better."
        ),
        "hallucination_gate": False,
    },
    "readability": {
        "label": "Structure & Readability",
        "description": (
            "The summary is logically organised with appropriate sections, "
            "headings, paragraph breaks, and sequence consistent with the template. "
            "Output must be render-safe: no stray JSON/XML/HTML, no broken tags, "
            "no raw markup unless explicitly required by the template. "
            "Score 5 = template followed precisely, logical flow, clean render-safe "
            "text. Score 1 = no discernible structure or render-breaking artefacts."
        ),
        "hallucination_gate": False,
    },
    "auditability": {
        "label": "Citation Quality",
        "description": (
            "Substantive claims are attributable to named speakers with timestamps "
            "where required. Citations must be short and targeted (a pointer, not "
            "a transcript dump) so a reviewer can verify claims quickly. "
            "Score 5 = all claims attributed correctly with speaker role/name and "
            "accurate timestamps; fully auditable. "
            "Score 1 = no attributions; all statements unverifiable without "
            "re-listening to the full recording."
        ),
        "hallucination_gate": False,
    },
}

# ---------------------------------------------------------------------------
# Gating thresholds (HLD section 4)
# ---------------------------------------------------------------------------

CRITICAL_DIMENSIONS: frozenset[str] = frozenset(
    {"accuracy", "action_clarity", "numerical_accuracy"}
)
CRITICAL_THRESHOLD: int = 4   # critical dim score < this → human review
REVIEW_THRESHOLD: int = 2     # any dim score ≤ this → review required
FAIL_THRESHOLD: int = 1       # any dim score == this → fail / block deployment


# ---------------------------------------------------------------------------
# Public prompt builders
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """Render and return the SYSTEM turn for the LLM judge."""
    template = _env.get_template("system_prompt.j2")
    return template.render(
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
