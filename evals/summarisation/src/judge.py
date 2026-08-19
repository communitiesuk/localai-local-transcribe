from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from common.canaries import wrap_with_canary
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
    intended_solicitation: str | None = None,
    marker_hash: str = "",
) -> str:
    """Render and return the SYSTEM turn, which is the same for every dimension.

    The dimension being scored is not named here: it is the only thing that varies between the judge
    calls for one summary, so it goes last, at the end of the user turn, where it cannot displace
    the shared prompt prefix the provider caches.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set,
    the template adds anti-injection hardening instructions that don't apply to ordinary judging.
    ``marker_hash`` must match the hash passed to the corresponding ``build_user_message`` call so
    the judge can tell genuine transcript/summary boundary markers from injected fakes.
    """
    template = _env.get_template("system_prompt.j2")
    return template.render(
        intended_solicitation=intended_solicitation,
        marker_hash=marker_hash,
    )


def build_user_message(
    *,
    target_dimension: str,
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

    Everything shared by the judge calls for one summary comes first and the rubric for
    ``target_dimension`` comes last, so those calls differ only in their tail and the provider can
    serve the transcript and summary from its prompt cache.

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
        target_dimension=target_dimension,
        citation_markers=citation_markers(summary_text, transcript_entry_count(transcript_text)),
        summary_id=summary_id,
        transcript_ref=transcript_ref,
        wrapped_transcript=wrap_with_canary("transcript", transcript_text, marker_hash),
        wrapped_summary=wrap_with_canary("summary", summary_text, marker_hash),
        template_name=template_name,
        template_content=template_content,
        wrapped_template=wrap_with_canary("custom-template", template_content, marker_hash)
        if template_content is not None
        else None,
        intended_solicitation=intended_solicitation,
        marker_hash=marker_hash,
    )
