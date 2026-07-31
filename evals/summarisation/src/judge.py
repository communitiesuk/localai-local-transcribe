from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from evals.summarisation.src.constants import CRITICAL_DIMENSIONS, DIMENSIONS
from evals.summarisation.src.transcript import citation_markers, transcript_entry_count

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"
_env = Environment(
    autoescape=True,
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_system_prompt(
    target_dimension: str | None = None,
    intended_solicitation: str | None = None,
    marker_hash: str = "",
) -> str:
    """Render and return the SYSTEM turn for a single specific dimension.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set,
    the template adds anti-injection hardening instructions that don't apply to ordinary judging.
    ``marker_hash`` must match the hash passed to the corresponding ``build_user_message`` call so
    the judge can tell genuine transcript/summary boundary markers from injected fakes.
    """
    template = _env.get_template("system_prompt.j2")
    return template.render(
        target_dimension=target_dimension,
        dimensions=DIMENSIONS,
        critical_dimensions=sorted(CRITICAL_DIMENSIONS),
        intended_solicitation=intended_solicitation,
        marker_hash=marker_hash,
    )


def build_user_message(
    *,
    summary_id: str,
    transcript_ref: str,
    transcript_text: str,
    summary_text: str,
    template_name: str | None = None,
    template_content: str | None = None,
    intended_solicitation: str | None = None,
    marker_hash: str,
) -> str:
    """Render and return the USER turn for the LLM judge.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set, the
    template adds a block telling the judge an injection is present and what it is trying to do.
    ``template_content`` is supplied only by the custom-template security vector, where the injection
    lives in a user-supplied template rather than the transcript; when set, the template is shown to
    the judge as the format the summary should adhere to and as the surface the injection came from.
    ``marker_hash`` is a short random hash generated fresh for this evaluation; it tags the
    transcript/summary boundary markers so the judge can't be fooled by text in the transcript or
    summary that mimics a marker (it won't know the hash in advance).

    The summary's citation markers are extracted mechanically and stated in the message. Left to
    read them off the summary itself, the judge confabulates markers that aren't there and credits
    the summary for them — so which markers exist is settled before it is asked to judge them. Only
    markers that resolve to an entry of ``transcript_text`` are listed, so an ordinary bracketed
    number in the summary is not passed off to the judge as a citation.
    """
    template = _env.get_template("user_message.j2")
    return template.render(
        citation_markers=citation_markers(summary_text, transcript_entry_count(transcript_text)),
        summary_id=summary_id,
        transcript_ref=transcript_ref,
        transcript_text=transcript_text,
        summary_text=summary_text,
        template_name=template_name,
        template_content=template_content,
        intended_solicitation=intended_solicitation,
        marker_hash=marker_hash,
    )
