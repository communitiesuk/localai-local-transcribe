from __future__ import annotations

import hashlib
import secrets
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from evals.summarisation.src.constants import DIMENSIONS, MARKER_BYTES
from evals.summarisation.src.transcript import citation_markers, transcript_entry_count

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"
_env = Environment(
    # These templates render plain-text LLM prompts, not markup. Escaping would rewrite the very
    # wording being judged — an apostrophe in a speaker's name becomes ``&#39;`` — and the judge
    # would score the summary against a corrupted transcript.
    autoescape=False,  # noqa: S701 - see above; these render prompts, not markup
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

# Marker per transcript, keyed on a digest so a transcript is never itself retained. Never evicted:
# a transcript that lost its marker mid-run would be issued a new one, and the two prompts of a
# single judge call would then disagree about which boundary is genuine.
_MARKERS: dict[str, str] = {}


def judge_marker_hash(transcript_text: str) -> str:
    """Boundary marker tagging the BEGIN/END lines of one transcript's judge prompts.

    Random, not derived from the transcript: an injection that could compute the marker could forge a
    boundary. Stable per transcript within a process, so one transcript's judge calls share a prompt
    prefix; a fresh process draws a fresh marker. ``setdefault`` does the lookup and the insert in one
    atomic step, so concurrent callers on one transcript cannot be handed different markers.
    """
    digest = hashlib.sha256(transcript_text.encode()).hexdigest()
    return _MARKERS.setdefault(digest, secrets.token_hex(MARKER_BYTES))


def build_system_prompt(*, marker_hash: str, intended_solicitation: str | None = None) -> str:
    """Render and return the SYSTEM turn for the LLM judge.

    Identical for every judge call on one transcript, so it sits inside that transcript's shared
    prefix. ``marker_hash`` is required, not defaulted: this is the judge's only trusted copy of the
    marker, and without it the real boundary value would be declared solely in the untrusted user
    turn. ``intended_solicitation`` is set only by the security eval, which adds anti-injection
    hardening.
    """
    template = _env.get_template("system_prompt.j2")
    return template.render(marker_hash=marker_hash, intended_solicitation=intended_solicitation)


def build_user_message(
    *,
    summary_id: str,
    transcript_ref: str,
    transcript_text: str,
    summary_text: str,
    target_dimension: str | None = None,
    template_name: str | None = None,
    template_content: str | None = None,
    intended_solicitation: str | None = None,
    marker_hash: str,
) -> str:
    """Render and return the USER turn for the LLM judge.

    Ordered static guidance, template, transcript, summary, rubric — coarsest-varying first, so the
    prefix shared between a transcript's judge calls reaches as far as possible.
    ``target_dimension`` selects the rubric; unset, every dimension is scored in one call.

    That shared prefix only buys anything *within* one transcript. The marker is drawn per transcript
    and stated in the second line of the system turn, so two transcripts share ~39 tokens; and the
    static preamble either side of it is ~650 tokens, under the 1024-token minimum a provider needs
    before it will cache a prefix at all. Shortening the preamble therefore cannot unlock
    cross-transcript caching, and lengthening it past 1024 would only help if the marker moved out of
    the prefix too.

    ``intended_solicitation`` and ``template_content`` are set only by the security eval, and add
    blocks naming the injection and the template it came from. ``marker_hash`` tags the transcript,
    summary and rubric boundaries; see :func:`judge_marker_hash`.

    Citation markers are extracted mechanically and stated in the message: left to read them off the
    summary itself, the judge invents markers and credits the summary for them. Only markers
    resolving to a transcript entry are listed.
    """
    template = _env.get_template("user_message.j2")
    return template.render(
        citation_markers=citation_markers(summary_text, transcript_entry_count(transcript_text)),
        summary_id=summary_id,
        transcript_ref=transcript_ref,
        transcript_text=transcript_text,
        summary_text=summary_text,
        target_dimension=target_dimension,
        dimensions=DIMENSIONS,
        template_name=template_name,
        template_content=template_content,
        intended_solicitation=intended_solicitation,
        marker_hash=marker_hash,
    )
