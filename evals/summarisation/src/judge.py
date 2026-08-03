from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from evals.summarisation.src.constants import DIMENSIONS, MARKER_BYTES, MARKER_CACHE_SIZE
from evals.summarisation.src.transcript import citation_markers, transcript_entry_count

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"
_env = Environment(
    # These templates render plain-text LLM prompts, not markup. Escaping would rewrite the very
    # wording being judged — an apostrophe in a speaker's name becomes ``&#39;`` — and the judge
    # would score the summary against a corrupted transcript.
    autoescape=False,  # noqa: S701
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


@lru_cache(maxsize=MARKER_CACHE_SIZE)
def judge_marker_hash(transcript_text: str) -> str:  # noqa: ARG001 - the memo key, see below
    """Boundary marker tagging the BEGIN/END lines of one transcript's judge prompts.

    Random, not derived from the transcript: an injection that could compute the marker could forge a
    boundary. Memoised per transcript so every judge call on it shares a cacheable prompt prefix.
    ``transcript_text`` is the cache key, not an input to the value.
    """
    return secrets.token_hex(MARKER_BYTES)


def build_system_prompt(*, marker_hash: str, intended_solicitation: str | None = None) -> str:
    """Render and return the SYSTEM turn for the LLM judge.

    Identical for every judge call on one transcript, so it sits inside the cacheable prefix.
    ``marker_hash`` is required, not defaulted: this is the judge's only trusted copy of the marker,
    and without it the real boundary value would be declared solely in the untrusted user turn.
    ``intended_solicitation`` is set only by the security eval, which adds anti-injection hardening.
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
    cacheable prefix reaches as far as possible. ``target_dimension`` selects the rubric; unset,
    every dimension is scored in one call.

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
