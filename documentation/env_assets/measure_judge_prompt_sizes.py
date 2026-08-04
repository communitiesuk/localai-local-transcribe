"""Measure the judge prompt's segment sizes and prefix sharing, for the token/cost model.

Read-only: renders the real templates locally and counts words/tokens. No API calls.

Segments matter because Azure caches an exact prefix from token 0. The judge prompt is laid out so
everything shared by one summary's per-dimension calls comes first and the rubric comes last, so:

  * across the 8 dimensions of one summary, the shared prefix runs up to the dimension name;
  * across summaries of the same transcript (bias eval iterations/variants), it runs up to the end
    of the transcript.

    poetry run python documentation/env_assets/measure_judge_prompt_sizes.py
"""

from __future__ import annotations

import tiktoken

from evals.summarisation.src.constants import DIMENSIONS
from evals.summarisation.src.judge import build_system_prompt, build_user_message

MIN_CACHEABLE_TOKENS = 1024
CACHE_BLOCK_TOKENS = 128

DIMS = list(DIMENSIONS)

_ENC = tiktoken.get_encoding("o200k_base")

MARKER = "deadbeef"
TRANSCRIPT_WORDS = 9000  # L in the model: a ~1 hour meeting


def _tokens(text: str) -> int:
    return len(_ENC.encode(text))


def _words(text: str) -> int:
    return len(text.split())


def _line(entry: int, seed: int) -> str:
    return f"[{entry}] Officer: item {entry} of meeting {seed} covered the costs and the agreed next steps"


def _transcript(words: int, seed: int = 0) -> str:
    """Numbered `[n] Speaker: utterance` entries totalling roughly ``words`` words."""
    per_line = _words(_line(0, seed))
    return "\n".join(_line(e, seed) for e in range(round(words / per_line)))


def _summary(words: int, seed: int = 0) -> str:
    sentence = f"The committee agreed the meeting {seed} budget and confirmed the deadline [3].\n"
    return sentence * round(words / _words(sentence))


def _call(dim: str, seed: int = 0) -> str:
    transcript = _transcript(TRANSCRIPT_WORDS, seed)
    return build_system_prompt(marker_hash=MARKER) + build_user_message(
        target_dimension=dim,
        summary_id=f"s{seed}",
        transcript_ref=f"t{seed}",
        transcript_text=transcript,
        summary_text=_summary(round(TRANSCRIPT_WORDS * 0.5), seed),
        marker_hash=MARKER,
    )


def _shared_prefix_chars(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


def _cacheable(shared_tokens: int) -> int:
    if shared_tokens < MIN_CACHEABLE_TOKENS:
        return 0
    return shared_tokens // CACHE_BLOCK_TOKENS * CACHE_BLOCK_TOKENS


def main() -> None:
    transcript = _transcript(TRANSCRIPT_WORDS)
    summary = _summary(round(TRANSCRIPT_WORDS * 0.5))
    system = build_system_prompt(marker_hash=MARKER)

    print(f"transcript: {_words(transcript):,} w / {_tokens(transcript):,} tok")
    print(f"summary:    {_words(summary):,} w / {_tokens(summary):,} tok")
    print(f"system:     {_words(system):,} w / {_tokens(system):,} tok")

    print("\nper-rubric size (words / tokens of the whole call)")
    for dim in DIMS:
        call = _call(dim)
        print(f"  {dim:<24}{_words(call):>8,} w{_tokens(call):>9,} tok")

    base = _call(DIMS[0])
    print("\nfixed wrapper (call minus transcript minus summary)")
    wrapper_w = _words(base) - _words(transcript) - _words(summary)
    print(f"  {wrapper_w:,} w  (system + preamble + citation block + rubric tail + rubric)")

    print("\nwrapper segments, in prompt order")
    body = build_user_message(
        target_dimension=DIMS[0],
        summary_id="s0",
        transcript_ref="t0",
        transcript_text=transcript,
        summary_text=summary,
        marker_hash=MARKER,
    )
    preamble = body[: body.index(f"BEGIN transcript {MARKER}")]
    between = body[body.index(f"END transcript {MARKER}") : body.index(f"BEGIN rubric {MARKER}")]
    between_fixed = _words(between) - _words(summary)
    rubric = body[body.index(f"BEGIN rubric {MARKER}") :]
    print(f"  system turn                      {_words(system):>6,} w")
    print(f"  preamble, above the transcript   {_words(preamble):>6,} w")
    print(f"  between transcript and rubric    {between_fixed:>6,} w  (excl. the summary itself)")
    print(f"  rubric block, this dimension     {_words(rubric):>6,} w")

    print("\nprefix shared across the 8 dimensions of one summary")
    same = [_call(d) for d in DIMS]
    across_dims = min(_shared_prefix_chars(same[0], c) for c in same[1:])
    pref_tok = _tokens(same[0][:across_dims])
    print(f"  {across_dims:,} chars / {pref_tok:,} tok cacheable={_cacheable(pref_tok):,}")
    print(f"  = {100 * _cacheable(pref_tok) / _tokens(same[0]):.1f}% of a {_tokens(same[0]):,} tok call")
    fixed_in_prefix = _words(same[0][:across_dims]) - _words(transcript) - _words(summary)
    print(f"  fixed text inside the prefix: {fixed_in_prefix:,} w (sys + preamble + pre-dimension mid)")
    print(f"  hence below the divergence point: {wrapper_w - fixed_in_prefix:,} w (rubric + its lead-in)")

    print("\nprefix shared across two summaries of the same transcript")
    other = build_system_prompt(marker_hash=MARKER) + build_user_message(
        target_dimension=DIMS[0],
        summary_id="s0",
        transcript_ref="t0",
        transcript_text=transcript,
        summary_text=_summary(round(TRANSCRIPT_WORDS * 0.5), seed=1),
        marker_hash=MARKER,
    )
    across_summaries = _shared_prefix_chars(same[0], other)
    pref2 = _tokens(same[0][:across_summaries])
    print(f"  {across_summaries:,} chars / {pref2:,} tok cacheable={_cacheable(pref2):,}")
    print(f"  = {100 * _cacheable(pref2) / _tokens(same[0]):.1f}% of a call")


if __name__ == "__main__":
    main()
