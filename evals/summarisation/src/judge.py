from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from common.settings import get_settings
from evals.summarisation.src.constants import DIMENSIONS
from evals.summarisation.src.transcript import citation_markers, transcript_entry_count

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompts"
_env = Environment(
    autoescape=True,
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

# How much of the transcript the marker hash is derived from. A leading sample plus the total length
# is enough to make the hash transcript-specific without digesting a multi-megabyte transcript on
# every judge call.
_MARKER_HASH_SAMPLE_CHARS = 4096

# Hex characters of digest kept, matching the width of the ``secrets.token_hex(4)`` hash this
# replaced. The hash only has to be unguessable in advance, not collision-proof.
_MARKER_HASH_CHARS = 8


@lru_cache(maxsize=1)
def _warn_marker_secret_missing() -> None:
    logger.warning(
        "JUDGE_MARKER_SECRET is not set: falling back to a random boundary-marker hash per judge "
        "call. The judge prompt then differs on every call and no prompt-prefix caching is possible."
    )


def judge_marker_hash(transcript_text: str) -> str:
    """Boundary-marker hash tagging the transcript/summary BEGIN/END lines of one judge prompt.

    The hash exists so the judge can tell a genuine boundary line from one injected into the
    transcript or summary: only lines carrying this hash are real. That requires the hash to be
    unguessable to whoever wrote the transcript, which a plain digest of the transcript is not —
    the transcript is exactly the text an injection controls, so an attacker could compute it. It is
    therefore keyed with ``JUDGE_MARKER_SECRET``, which lives outside the data being judged.

    Deriving it from the transcript rather than drawing it fresh per call is what makes the prompt
    cacheable. Every judge call on one transcript then shares a byte-identical prefix up to the end
    of the transcript, so a provider prefix cache hits on the largest block in the prompt. A
    per-call random hash sat ahead of the transcript and invalidated it every time.

    The summary is deliberately not hashed in: the hash is printed before the transcript, so making
    it depend on the summary would break that shared prefix for every summary of a transcript.

    With no secret configured the hash would be forgeable, so caching is dropped rather than the
    guarantee: a fresh random hash is returned per call and a warning is logged once.
    """
    secret = get_settings().JUDGE_MARKER_SECRET
    if not secret:
        _warn_marker_secret_missing()
        return secrets.token_hex(_MARKER_HASH_CHARS // 2)

    sample = f"{len(transcript_text)}:{transcript_text[:_MARKER_HASH_SAMPLE_CHARS]}"
    digest = hmac.new(secret.encode(), sample.encode(), hashlib.sha256).hexdigest()
    return digest[:_MARKER_HASH_CHARS]


def build_system_prompt(intended_solicitation: str | None = None) -> str:
    """Render and return the SYSTEM turn for the LLM judge.

    The turn is identical for every judge call in a run: the rubric being scored, the transcript, the
    summary and the marker hash all live in the user turn, so nothing here varies per call and the
    whole system turn sits inside the cacheable prefix.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set,
    the template adds anti-injection hardening instructions that don't apply to ordinary judging.
    """
    template = _env.get_template("system_prompt.j2")
    return template.render(intended_solicitation=intended_solicitation)


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

    The turn is ordered criterion, template, transcript, summary — coarsest-varying content first,
    so the prompt prefix a provider can cache reaches as far as possible. The criterion leads so the
    judge reads the rubric before the evidence it has to weigh; everything that changes per summary
    (its identifier, its citation markers, the summary itself) is pushed to the tail, behind the
    transcript. ``target_dimension`` selects the rubric; left unset, every dimension is scored in one
    call.

    ``intended_solicitation`` is supplied only by the security (prompt-injection) eval; when set, the
    template adds a block telling the judge an injection is present and what it is trying to do.
    ``template_content`` is supplied only by the custom-template security vector, where the injection
    lives in a user-supplied template rather than the transcript; when set, the template is shown to
    the judge as the format the summary should adhere to and as the surface the injection came from.
    ``marker_hash`` tags the transcript/summary boundary markers so the judge can't be fooled by text
    in the transcript or summary that mimics a marker; see :func:`judge_marker_hash`.

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
