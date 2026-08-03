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

    The marker exists so the judge can tell a genuine boundary line from one injected into the
    transcript, summary or template: only lines carrying this marker are real. That requires the
    marker to be unguessable to whoever wrote the transcript, so it is drawn from the CSPRNG rather
    than derived from the text being judged — a digest of the transcript would be computable by the
    very injection it is meant to defeat.

    Memoising it against the transcript is what makes the prompt cacheable. Every judge call on one
    transcript shares a byte-identical prefix through the transcript and summary, so a provider
    prefix cache hits on the largest blocks in the prompt. Drawing a marker per *call* instead put
    fresh bytes ahead of the transcript and invalidated the prefix every time.

    A new process draws new markers, so a marker that leaks — into a judge rationale, a prompt dump,
    a published eval artifact — expires with the run rather than staying valid for that transcript
    forever. ``transcript_text`` is the cache key, not an input to the value.
    """
    return secrets.token_hex(MARKER_BYTES)


def build_system_prompt(*, marker_hash: str, intended_solicitation: str | None = None) -> str:
    """Render and return the SYSTEM turn for the LLM judge.

    The turn is identical for every judge call on one transcript: the rubric, the transcript and the
    summary all live in the user turn, so nothing here varies across that transcript's calls and the
    whole system turn sits inside the cacheable prefix. Transcripts share no prefix anyway, so naming
    the transcript's marker here costs no caching.

    ``marker_hash`` is required rather than defaulted because this is the judge's only trusted copy
    of the marker. Without it the sole declaration of the real boundary value would sit in the user
    turn, alongside the text trying to forge one, with nothing to check a rival declaration against.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set,
    the template adds anti-injection hardening instructions that don't apply to ordinary judging.
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

    The turn is ordered static guidance, template, transcript, summary, rubric — coarsest-varying
    content first, so the prompt prefix a provider can cache reaches as far as possible. The rubric
    goes last because the dimension varies fastest: a run scores one summary against several
    dimensions, and with the rubric at the tail those calls share a prefix that already contains the
    transcript and the summary. The system turn tells the judge to read the rubric first, so putting
    it last costs nothing in reading order. ``target_dimension`` selects the rubric; left unset,
    every dimension is scored in one call.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set, the
    template adds a block telling the judge an injection is present and what it is trying to do.
    ``template_content`` is supplied only by the custom-template security vector, where the injection
    lives in a user-supplied template rather than the transcript; when set, the template is shown to
    the judge as the format the summary should adhere to and as the surface the injection came from.
    ``marker_hash`` tags the transcript, summary and rubric boundaries so the judge can't be fooled
    by text that mimics one — including text posing as a second rubric, which matters now that the
    rubric shares a turn with the data; see :func:`judge_marker_hash`.

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
        target_dimension=target_dimension,
        dimensions=DIMENSIONS,
        template_name=template_name,
        template_content=template_content,
        intended_solicitation=intended_solicitation,
        marker_hash=marker_hash,
    )
