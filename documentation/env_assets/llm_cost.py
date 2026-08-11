"""Per-meeting LLM token usage and GBP cost for the production model pairing.

Companion to llm_inference.py, which models output tokens only (all EcoLogits needs).
Cost needs input tokens too, so every invocation here carries (uncached input,
cacheable input, output) tokens.

Headline figures are the usage-weighted average over the production template shares in
assumptions.yaml. Call graphs traced from common/prompts.py, common/templates/ and
common/llm/client.py; prompt sizes counted from the live prompt files, not the Appendix B
figures in env-impact.md, which have drifted (general.j2 is 579 words now, not 345).
"""

from dataclasses import dataclass

# =============================================================================
# Token model (Appendix B.1 convention: X transcript words, 2 tokens per word)
# =============================================================================

WORDS_PER_HOUR = 9_000  # Appendix B.1 X, for a 1-hour meeting
ENTRIES_PER_HOUR = 450  # dialogue entries
TOK = 2  # tokens per word

HTML = 1.25  # markdown -> HTML tag inflation; the guardrail sees the HTML minute


@dataclass(frozen=True)
class Meeting:
    """Transcript sizes for a meeting of a given audio duration. Everything scales
    linearly with duration: nothing in the prompts caps minute length, so a 3-hour
    meeting is modelled as producing a 3x longer minute."""

    hours: float

    @property
    def words(self) -> float:
        return WORDS_PER_HOUR * self.hours

    @property
    def xt(self) -> float:
        """Transcript words as tokens, before speaker labels."""
        return self.words * TOK

    @property
    def t(self) -> float:
        """transcript_as_speaker_and_utterance. Renderings come from
        common/format_transcript.py; every entry carries a speaker label
        ("Speaker 3: " + newline, ~5 tokens)."""
        return self.xt + ENTRIES_PER_HOUR * self.hours * 5

    @property
    def t_idx(self) -> float:
        """transcript_as_index_speaker_and_utterance, + an index ("[212] ", ~3 tokens)."""
        return self.t + ENTRIES_PER_HOUR * self.hours * 3


# Prompt files and inline prompts, words -> tokens
P_GENERAL = 579 * TOK  # general.j2
P_EXEC = 129 * TOK  # executive_summary.j2
P_EXTRACT = 463 * TOK  # extract_claims.j2
P_CITE = 315 * TOK  # cite_claims.j2
P_SECTIONS = 69 * TOK  # sections_from_transcript.j2
P_SECTION_FOR = 15 * TOK  # section_for_agenda.j2
P_DELIVERY_SYS = 30 * TOK  # inline system message in delivery.py
P_DELIVERY_STYLE = 161 * TOK  # delivery_style_guide.j2 + wrapper
P_DOCUMENT = (115 + 200 + 7) * TOK  # document_prompt fixed + assumed user content + date
P_SPEAKER = (63 + 30) * TOK  # inline system + user in generate_speaker_predictions.py
P_TITLE = 14 * TOK  # meeting_title.j2
P_GUARDRAIL = 85 * TOK  # inline system + wrapper in get_accuracy_check_messages

Y = 6  # sections, SectionTemplate

# Pessimism knobs.
# No call site sets reasoning_effort, so both GPT-5.x models emit reasoning tokens that
# are billed as output on top of the visible answer.
REASONING = 1.15
# Azure caches in 128-token blocks, evicts after 5-10 min idle, and never serves the
# first request of a chain, so a replayed prefix does not bill as 100% cache hit.
CACHE_HIT = 0.75

# =============================================================================
# Pricing: GBP per 1M tokens, (input, cached input, output).
# Azure OpenAI Sweden Central Data Zone list price:
# https://azure.microsoft.com/en-us/pricing/details/azure-openai/
# =============================================================================

PRICES = {
    "best": (1.04, 0.11, 8.28),  # gpt-5.1  (BEST_LLM_MODEL_NAME)
    "fast": (0.04, 0.01, 0.31),  # gpt-5-nano (FAST_LLM_MODEL_NAME)
}

# Azure AI Speech standard transcription, UK South, GBP per hour of audio:
# https://azure.microsoft.com/en-us/pricing/details/speech/
SPEECH_GBP_PER_HOUR = {
    "realtime": 0.753,
    "fast": 0.271,
    "batch": 0.136,
}


@dataclass
class Inv:
    """One API invocation. cacheable_in is prefix a previous call in the same
    conversation already sent verbatim, so Azure can serve it from cache."""

    name: str
    tier: str  # "fast" | "best"
    new_in: float
    cacheable_in: float
    out: float


def _common(m: Meeting, minute_tokens: float) -> list[Inv]:
    """Calls every standard meeting makes regardless of template.

    Speaker ID, title and the guardrail each re-send the whole transcript behind a
    different leading message, so none of them can hit another's cached prefix.
    """
    return [
        Inv("speaker_id", "fast", P_SPEAKER + m.t, 0, 80),
        Inv("title", "fast", P_TITLE + m.t, 0, 20),
        Inv("accuracy_guardrail", "fast", P_GUARDRAIL + m.t + minute_tokens * HTML, 0, 200),
    ]


def _citations(m: Meeting, draft: float, claims: float) -> list[Inv]:
    """extract_claims + cite_claims (both FAST, both fresh conversations). cite_claims
    echoes every claim back in claim_citations, so its output is the cited draft plus
    the claim list again."""
    return [
        Inv("extract_claims", "fast", P_EXTRACT + draft, 0, claims),
        Inv("cite_claims", "fast", P_CITE + m.t_idx + claims + draft, 0, draft * 1.05 + claims + 300),
    ]


def general(m: Meeting) -> list[Inv]:
    """General / Care Assessment / Care Assessment V2 — SimpleTemplate with citations."""
    draft, claims = 0.5 * m.xt, 0.1 * m.xt
    return [
        Inv("minutes", "best", P_GENERAL + m.t, 0, draft),
        *_citations(m, draft, claims),
        *_common(m, draft * 1.05),
    ]


def executive_summary(m: Meeting) -> list[Inv]:
    """Short 'n' Sweet — SimpleTemplate, citations_required = False."""
    draft = 0.3 * m.xt
    return [
        Inv("minutes", "best", P_EXEC + m.t, 0, draft),
        *_common(m, draft),
    ]


def delivery(m: Meeting) -> list[Inv]:
    """Delivery — sections then attendees, then citations.

    ChatBot.structured_chat sends only the messages handed to it (unlike ChatBot.chat, it
    ignores self.messages), so the attendees call replays nothing: no transcript, and so
    nothing to cache either.
    """
    sections_out = 0.4 * m.xt + 60
    draft = sections_out + 300  # + attendee/action header
    return [
        Inv("delivery_sections", "best", P_DELIVERY_SYS + m.t + P_DELIVERY_STYLE, 0, sections_out),
        Inv("delivery_attendees", "best", 20, 0, 300),
        *_citations(m, draft, 0.08 * m.xt),
        *_common(m, draft * 1.05),
    ]


def user_template_document(m: Meeting) -> list[Inv]:
    """UserTemplate DOCUMENT — single BEST generation, no citations."""
    draft = 0.5 * m.xt
    return [
        Inv("document_generation", "best", P_DOCUMENT + m.t, 0, draft),
        *_common(m, draft),
    ]


def section_template(m: Meeting) -> list[Inv]:
    """SectionTemplate (Cabinet / Planning Committee) — Y BEST calls on one accumulating
    ChatBot.chat conversation, so each call after the first replays the previous request
    verbatim and the transcript is paid for at full price once. No concrete
    implementation survives in common/templates, so the system prompt is assumed to be
    general.j2-sized.
    """
    per_section = 0.3 * m.xt / Y
    first_request = P_GENERAL + m.t + P_SECTION_FOR
    invs = [
        Inv("section_detection", "fast", P_SECTIONS + m.t, 0, 2 * Y * TOK),
        Inv("section_1", "best", first_request, 0, per_section),
    ]
    request_len: float = first_request
    for k in range(2, Y + 1):
        # The previous assistant reply plus the new request are new input; everything
        # before them was sent verbatim last call.
        new_in = per_section + P_SECTION_FOR
        invs.append(Inv(f"section_{k}", "best", new_in, request_len, per_section))
        request_len += new_in
    draft = 0.3 * m.xt
    invs += _citations(m, draft, 0.06 * m.xt)
    invs += _common(m, draft * 1.05)
    return invs


TEMPLATES = {
    "General": general,
    "Short 'n' Sweet": executive_summary,
    "Delivery": delivery,
    "User generated (DOCUMENT)": user_template_document,
    "SectionTemplate (Y=6)": section_template,
}

# Production shares (Appendix F.1), mapped onto the five implementations above.
SHARES = {
    "General": 0.5241 + 0.0261 + 0.0073,  # + Care Assessment, Care Assessment V2
    "Delivery": 0.1523,
    "Short 'n' Sweet": 0.1234,
    "User generated (DOCUMENT)": 0.0960,
    "SectionTemplate (Y=6)": 0.0589 + 0.0120,  # Cabinet + Planning Committee
}

# Full transcript copies sent per meeting, (FAST, BEST).
TRANSCRIPT_COPIES: dict[str, tuple[float, float]] = {
    "General": (4, 1),  # speaker, title, cite_claims, guardrail | minutes
    "Short 'n' Sweet": (3, 1),  # speaker, title, guardrail | minutes
    "Delivery": (4, 1),  # speaker, title, cite_claims, guardrail | sections
    "User generated (DOCUMENT)": (3, 1),  # speaker, title, guardrail | document
    "SectionTemplate (Y=6)": (5, 1),  # + section_detection | section_1
}
TRANSCRIPT_COPIES["Usage-weighted"] = (
    sum(SHARES[n] * TRANSCRIPT_COPIES[n][0] for n in SHARES),
    sum(SHARES[n] * TRANSCRIPT_COPIES[n][1] for n in SHARES),
)

# Transcript replays that could become cache hits if prompts led with the same currently
# compatible transcript block, excluding the first copy that has to populate the cache.
# Speaker ID uses pre-prediction labels ("Unknown speaker N"), cite_claims uses indexed
# transcript lines, and FAST calls cannot seed BEST cache entries.
CACHEABLE_TRANSCRIPT_REPLAYS: dict[str, tuple[float, float]] = {
    "General": (1, 0),  # title -> guardrail
    "Short 'n' Sweet": (1, 0),  # title -> guardrail
    "Delivery": (1, 0),  # title -> guardrail
    "User generated (DOCUMENT)": (1, 0),  # title -> guardrail
    "SectionTemplate (Y=6)": (2, 0),  # section_detection -> title -> guardrail
}
CACHEABLE_TRANSCRIPT_REPLAYS["Usage-weighted"] = (
    sum(SHARES[n] * CACHEABLE_TRANSCRIPT_REPLAYS[n][0] for n in SHARES),
    sum(SHARES[n] * CACHEABLE_TRANSCRIPT_REPLAYS[n][1] for n in SHARES),
)


def tokens(invs: list[Inv]) -> dict[str, float]:
    """Billable tokens for one meeting, split by tier and by cache status."""
    agg: dict[str, float] = {"calls": len(invs)}
    for tier in ("fast", "best"):
        sel = [i for i in invs if i.tier == tier]
        agg[f"{tier}_calls"] = len(sel)
        agg[f"{tier}_new_in"] = sum(i.new_in for i in sel)
        agg[f"{tier}_cacheable_in"] = sum(i.cacheable_in for i in sel)
        agg[f"{tier}_out"] = sum(i.out for i in sel) * REASONING
    return _derive(agg)


def _derive(agg: dict[str, float]) -> dict[str, float]:
    for key in ("new_in", "cacheable_in", "out"):
        agg[key] = agg[f"fast_{key}"] + agg[f"best_{key}"]
    for prefix in ("fast_", "best_", ""):
        agg[f"{prefix}total_in"] = agg[f"{prefix}new_in"] + agg[f"{prefix}cacheable_in"]
        agg[f"{prefix}cached_in"] = agg[f"{prefix}cacheable_in"] * CACHE_HIT
        agg[f"{prefix}uncached_in"] = agg[f"{prefix}total_in"] - agg[f"{prefix}cached_in"]
    return agg


def weighted(m: Meeting) -> dict[str, float]:
    """Usage-weighted average across the production templates."""
    keys = [f"{t}_{k}" for t in ("fast", "best") for k in ("calls", "new_in", "cacheable_in", "out")]
    agg = dict.fromkeys([*keys, "calls"], 0.0)
    for name, share in SHARES.items():
        tk = tokens(TEMPLATES[name](m))
        for k in agg:
            agg[k] += share * tk[k]
    return _derive(agg)


def cost(tk: dict[str, float], *, caching: bool = True, only: str | None = None) -> float:
    """GBP for one meeting. caching=False bills every replayed prefix at full price.
    only="fast"/"best" restricts the total to that tier."""
    total = 0.0
    for tier in ("fast", "best") if only is None else (only,):
        p_in, p_cached, p_out = PRICES[tier]
        cached = tk[f"{tier}_cacheable_in"] * CACHE_HIT if caching else 0.0
        uncached = tk[f"{tier}_new_in"] + tk[f"{tier}_cacheable_in"] - cached
        total += (uncached * p_in + cached * p_cached + tk[f"{tier}_out"] * p_out) / 1e6
    return total


def headroom(tk: dict[str, float], name: str, m: Meeting) -> float:
    """Cost if compatible transcript replays were moved into a cacheable prefix.

    The first compatible transcript copy remains in new_in; only later copies are
    reclassified as cacheable. This counts the transcript body only, not small wrapper
    text around the block.
    """
    hypo = dict(tk)
    for tier, replays in zip(("fast", "best"), CACHEABLE_TRANSCRIPT_REPLAYS[name], strict=True):
        replay_tokens = m.t * replays
        hypo[f"{tier}_new_in"] -= replay_tokens
        hypo[f"{tier}_cacheable_in"] += replay_tokens
    return cost(hypo)


def display() -> None:
    one_hour = Meeting(1.0)
    model_labels = "BEST=gpt-5.1, FAST=gpt-5-nano"
    print(f"\nPer 1-hour meeting (X = {one_hour.words:,.0f} words, {TOK} tokens/word, {model_labels})")
    print("=" * 118)
    print(
        f"{'Template':<26} {'Calls':>5} {'In FAST':>10} {'In BEST':>10} {'Out FAST':>9}"
        f" {'Out BEST':>9} {'GBP FAST':>9} {'GBP BEST':>9} {'GBP total':>10} {'GBP no cache':>13}"
    )
    print("-" * 118)
    rows = {name: tokens(fn(one_hour)) for name, fn in TEMPLATES.items()}
    rows["Usage-weighted"] = weighted(one_hour)
    for name, tk in rows.items():
        if name == "Usage-weighted":
            print("-" * 118)
        print(
            f"{name:<26} {tk['calls']:>5.1f} {tk['fast_total_in']:>10,.0f} {tk['best_total_in']:>10,.0f}"
            f" {tk['fast_out']:>9,.0f} {tk['best_out']:>9,.0f}"
            f" {cost(tk, only='fast'):>9.4f} {cost(tk, only='best'):>9.4f}"
            f" {cost(tk):>10.4f} {cost(tk, caching=False):>13.4f}"
        )

    wt = rows["Usage-weighted"]
    c_cached, c_none = cost(wt), cost(wt, caching=False)
    print("\n\nHeadline: usage-weighted average meeting, split by tier")
    print("=" * 100)
    print(f"  {'':<44} {'FAST':>14} {'BEST':>14} {'Total':>14}")
    print("  " + "-" * 88)
    for label, key in [
        ("Calls", "calls"),
        ("Input tokens (total)", "total_in"),
        ("  of which cached", "cached_in"),
        ("  of which non-cached", "uncached_in"),
        (f"Output tokens (incl. {REASONING - 1:.0%} reasoning)", "out"),
    ]:
        fmt = ",.1f" if key == "calls" else ",.0f"
        print(f"  {label:<44} {wt[f'fast_{key}']:>14{fmt}} {wt[f'best_{key}']:>14{fmt}} {wt[key]:>14{fmt}}")
    print("  " + "-" * 88)
    for label, caching in [("Cost, caching as built (GBP)", True), ("Cost, caching off (GBP)", False)]:
        f_c = cost(wt, caching=caching, only="fast")
        b_c = cost(wt, caching=caching, only="best")
        print(f"  {label:<44} {f_c:>14.4f} {b_c:>14.4f} {f_c + b_c:>14.4f}")
    f_share, b_share = cost(wt, only="fast") / c_cached, cost(wt, only="best") / c_cached
    print(f"  {'Share of cost, caching as built':<44} {f_share:>13.0%} {b_share:>13.0%}")
    print(f"\n  {'Cost per 1,000 meetings, caching as built (GBP)':<48} {c_cached * 1e3:>10.2f}")
    print(
        f"\n  Caching only bites where one conversation replays a prefix (SectionTemplate), so"
        f"\n  turning it off costs {c_none / c_cached - 1:+.1%}. Moving currently compatible transcript"
        f"\n  replays into a shared prefix would instead land at GBP {headroom(wt, 'Usage-weighted', one_hour):.4f}"
        f" ({headroom(wt, 'Usage-weighted', one_hour) / c_cached - 1:+.0%})."
    )


if __name__ == "__main__":
    display()
