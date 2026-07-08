from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from evals.summarisation.src.constants import CRITICAL_DIMENSIONS, DIMENSIONS

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"
_env = Environment(
    autoescape=True,
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
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
    intended_solicitation: str | None = None,
) -> str:
    """Render and return the USER turn for the LLM judge.

    ``intended_solicitation`` is only supplied by the security (prompt-injection) eval: when set, the
    user message gains a block telling the judge an injection is present and what it is trying to do.
    """
    template = _env.get_template("user_message.j2")
    return template.render(
        summary_id=summary_id,
        transcript_ref=transcript_ref,
        transcript_text=transcript_text,
        summary_text=summary_text,
        template_name=template_name,
        intended_solicitation=intended_solicitation,
    )
