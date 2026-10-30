"""Sections 7 + Appendix B/F.2: LLM inference energy per template and usage-weighted average."""

from ecologits.impacts.llm import compute_llm_impacts

from utils import (
    GPT5_NANO_PARAMS_B,
    GPT5_NANO_TPS,
    GPT5_NANO_TTFT,
    GPT51_ACTIVE_B,
    GPT51_TOTAL_B,
    GPT51_TPS,
    GPT51_TTFT,
    LLM_CARBON_INTENSITY_G_PER_KWH,
    NUM_SECTIONS,
    OPENAI_PUE,
    OPENAI_WUE,
    TRANSCRIPT_WORDS,
    UK_ADPE,
    UK_GWP_KG_PER_KWH,
    UK_PE,
    UK_WUE,
    _cfg,
    _rng,
    _row,
    _section,
    words_to_tokens,
)

# =============================================================================
# Per-invocation EcoLogits model
# =============================================================================


def _inv(output_words: float, model: str) -> dict:
    """Compute EcoLogits impact for a single API invocation (output tokens only; TTFT covers prefill)."""
    output_tokens = words_to_tokens(output_words)
    if output_tokens == 0:
        return {"model": model, "out_tokens": 0.0, "wh_min": 0.0, "wh_max": 0.0, "gwp_g_min": 0.0, "gwp_g_max": 0.0}

    if model == "fast":
        active, total, tps, ttft = GPT5_NANO_PARAMS_B, GPT5_NANO_PARAMS_B, GPT5_NANO_TPS, GPT5_NANO_TTFT
    else:
        active, total, tps, ttft = GPT51_ACTIVE_B, GPT51_TOTAL_B, GPT51_TPS, GPT51_TTFT

    r = compute_llm_impacts(
        model_active_parameter_count=active,
        model_total_parameter_count=total,
        output_token_count=output_tokens,
        if_electricity_mix_adpe=UK_ADPE,
        if_electricity_mix_pe=UK_PE,
        if_electricity_mix_gwp=UK_GWP_KG_PER_KWH,
        if_electricity_mix_wue=UK_WUE,
        datacenter_pue=OPENAI_PUE,
        datacenter_wue=OPENAI_WUE,
        tps=tps,
        ttft=ttft,
    )
    wh_min = r.energy.value.min * 1000
    wh_max = r.energy.value.max * 1000
    return {
        "model": model,
        "out_tokens": output_tokens,
        "wh_min": wh_min,
        "wh_max": wh_max,
        "gwp_g_min": wh_min / 1000 * LLM_CARBON_INTENSITY_G_PER_KWH,
        "gwp_g_max": wh_max / 1000 * LLM_CARBON_INTENSITY_G_PER_KWH,
    }


def _combine(*invocations: dict) -> dict:
    """Aggregate per-invocation results into a template-level summary."""
    fast = [i for i in invocations if i["model"] == "fast"]
    best = [i for i in invocations if i["model"] == "best"]
    fast_wh_min = sum(i["wh_min"] for i in fast)
    fast_wh_max = sum(i["wh_max"] for i in fast)
    best_wh_min = sum(i["wh_min"] for i in best)
    best_wh_max = sum(i["wh_max"] for i in best)
    wh_min = fast_wh_min + best_wh_min
    wh_max = fast_wh_max + best_wh_max
    gwp_min = sum(i["gwp_g_min"] for i in invocations)
    gwp_max = sum(i["gwp_g_max"] for i in invocations)
    return {
        "fast_out_tokens": sum(i["out_tokens"] for i in fast),
        "best_out_tokens": sum(i["out_tokens"] for i in best),
        "total_out_tokens": sum(i["out_tokens"] for i in invocations),
        "fast_wh_min": fast_wh_min,
        "fast_wh_max": fast_wh_max,
        "best_wh_min": best_wh_min,
        "best_wh_max": best_wh_max,
        "total_wh_min": wh_min,
        "total_wh_max": wh_max,
        "total_wh": (wh_min + wh_max) / 2,
        "gwp_g_min": gwp_min,
        "gwp_g_max": gwp_max,
        "co2e_g": (gwp_min + gwp_max) / 2,
    }


# =============================================================================
# Template functions (Appendix B)
# =============================================================================


def simple_template(x: float = TRANSCRIPT_WORDS) -> dict:
    """B.2 — SimpleTemplate: General / Care Assessment / Care Assessment V2 (6 invocations)."""
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.5 * x, "best"),  # 3. minutes
        _inv(80, "best"),  # 4. hallucination check
        _inv(0.1 * x, "fast"),  # 5. extract_claims
        _inv(0.5 * x, "fast"),  # 6. cite_claims
    )


def section_template(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    """B.3 — SectionTemplate: Cabinet / Planning Committee (5 + 2Y invocations)."""
    section_words = 0.3 * x / y
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(2 * y, "fast"),  # 3. section detection
        *[_inv(section_words, "best") for _ in range(y)],  # 4×Y section outputs
        *[_inv(80, "best") for _ in range(y)],  # 5×Y hallucination checks
        _inv(0.06 * x, "fast"),  # 6. extract_claims
        _inv(0.3 * x, "fast"),  # 7. cite_claims
    )


def delivery_template(x: float = TRANSCRIPT_WORDS) -> dict:
    """B.4 — Delivery Template (6 invocations: 4 FAST + 2 BEST)."""
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.4 * x + 30, "best"),  # 3. sections + actions + attendees
        _inv(80, "best"),  # 4. hallucination check
        _inv(0.08 * x, "fast"),  # 5. extract_claims
        _inv(0.4 * x, "fast"),  # 6. cite_claims
    )


def basic_minutes(x: float = TRANSCRIPT_WORDS) -> dict:
    """B.5 — Basic Minutes fallback (4 FAST-only invocations)."""
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.3 * x, "fast"),  # 3. summary
        _inv(80, "fast"),  # 4. hallucination check
    )


def executive_summary(x: float = TRANSCRIPT_WORDS) -> dict:
    """B.2a — Short 'n' Sweet / ExecutiveSummary (4 invocations, no citations)."""
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.3 * x, "best"),  # 3. minutes
        _inv(80, "best"),  # 4. hallucination check
    )


def user_template_document(x: float = TRANSCRIPT_WORDS) -> dict:
    """B.6.1 — UserTemplate (DOCUMENT type): 4 invocations (2 FAST + 2 BEST)."""
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.5 * x, "best"),  # 3. document generation
        _inv(80, "best"),  # 4. hallucination check
    )


# =============================================================================
# Appendix F.2: usage-weighted impact
# =============================================================================

TEMPLATE_USAGE_SHARES: list[tuple[str, float, str]] = [
    (row["name"], row["share"], row["implementation"]) for row in _cfg["template_usage_shares"]
]

_TEMPLATE_FN = {
    "General": lambda x, y: simple_template(x),
    "Delivery": lambda x, y: delivery_template(x),
    "Short 'n' Sweet": lambda x, y: executive_summary(x),
    "User generated": lambda x, y: user_template_document(x),
    "Cabinet": lambda x, y: section_template(x, y),
    "Care Assessment": lambda x, y: simple_template(x),
    "Planning Committee": lambda x, y: section_template(x, y),
    "Care Assessment V2": lambda x, y: simple_template(x),
}


def usage_weighted_impact(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    """F.2.3 — Usage-weighted average LLM impact across all production templates."""
    wt_out_tokens = wt_wh_min = wt_wh_max = wt_gwp_min = wt_gwp_max = 0.0
    for name, share, _ in TEMPLATE_USAGE_SHARES:
        r = _TEMPLATE_FN[name](x, y)
        wt_out_tokens += share * r["total_out_tokens"]
        wt_wh_min += share * r["total_wh_min"]
        wt_wh_max += share * r["total_wh_max"]
        wt_gwp_min += share * r["gwp_g_min"]
        wt_gwp_max += share * r["gwp_g_max"]
    return {
        "total_out_tokens": wt_out_tokens,
        "total_wh_min": wt_wh_min,
        "total_wh_max": wt_wh_max,
        "total_wh": (wt_wh_min + wt_wh_max) / 2,
        "gwp_g_min": wt_gwp_min,
        "gwp_g_max": wt_gwp_max,
        "co2e_g": (wt_gwp_min + wt_gwp_max) / 2,
    }


# =============================================================================
# Public interface
# =============================================================================


def calculate(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    return {
        "simple_template": simple_template(x),
        "section_template": section_template(x, y),
        "delivery_template": delivery_template(x),
        "basic_minutes": basic_minutes(x),
        "executive_summary": executive_summary(x),
        "user_template_document": user_template_document(x),
        "usage_weighted": usage_weighted_impact(x, y),
        "by_template": {name: _TEMPLATE_FN[name](x, y) for name, _, _ in TEMPLATE_USAGE_SHARES},
    }


def display() -> None:
    r = calculate()
    st, sec, dv, bm = r["simple_template"], r["section_template"], r["delivery_template"], r["basic_minutes"]
    es, utd, wt = r["executive_summary"], r["user_template_document"], r["usage_weighted"]

    for title, tr, inv in [
        ("Section 7.1: SimpleTemplate", st, "6"),
        (f"Section 7.2: SectionTemplate Y={NUM_SECTIONS}", sec, f"5+2×{NUM_SECTIONS}={5 + 2 * NUM_SECTIONS}"),
        ("Section 7.3: Delivery Template", dv, "6"),
        ("Section 7.4: Basic Minutes (fallback)", bm, "4"),
    ]:
        _section(f"{title}  [{inv} invocations]")
        _row("GPT-5-nano (fast) output tokens", f"{tr['fast_out_tokens']:,.0f}")
        _row("GPT-5.1 (best) output tokens", f"{tr['best_out_tokens']:,.0f}")
        _row("Total output tokens", f"{tr['total_out_tokens']:,.0f}")
        _row("GPT-5-nano energy", _rng(tr["fast_wh_min"], tr["fast_wh_max"], "Wh"))
        _row("GPT-5.1 energy", _rng(tr["best_wh_min"], tr["best_wh_max"], "Wh"))
        _row(
            "Total LLM energy",
            f"{_rng(tr['total_wh_min'], tr['total_wh_max'], 'Wh')}"
            f"  ({_rng(tr['total_wh_min']/1000, tr['total_wh_max']/1000, 'kWh', dp=4)})",
        )
        _row("CO₂e (energy × GBR 217 g/kWh)", _rng(tr["gwp_g_min"], tr["gwp_g_max"], "g"))

    _section("Section 7.6: Template Comparison Summary")
    print(f"  {'Template':<34} {'Invocations':>11} {'Out Tokens':>10} {'Energy (Wh)':>20} {'CO₂e (g)':>16}")
    print(f"  {'-'*34} {'-'*11} {'-'*10} {'-'*20} {'-'*16}")
    for name, inv, tr in [
        ("Basic Minutes", "4", bm),
        ("Short 'n' Sweet (no citations)", "4", es),
        ("UserTemplate DOCUMENT", "4", utd),
        ("Delivery", "6", dv),
        ("SimpleTemplate", "6", st),
        (f"SectionTemplate Y={NUM_SECTIONS}", f"5+2×{NUM_SECTIONS}={5 + 2 * NUM_SECTIONS}", sec),
    ]:
        print(
            f"  {name:<34} {inv:>11} {tr['total_out_tokens']:>10,.0f}"
            f" {_rng(tr['total_wh_min'], tr['total_wh_max']):>20}"
            f" {_rng(tr['gwp_g_min'], tr['gwp_g_max']):>16}"
        )

    _section("Appendix F.2: Usage-Weighted Impact (production shares, Dec 2024–May 2026)")
    print(f"  {'Template':<28} {'Share':>6} {'Impl.':<38} {'Out Tok':>8} {'CO₂e (g)':>14}")
    print(f"  {'-'*28} {'-'*6} {'-'*38} {'-'*8} {'-'*14}")
    for tname, share, impl in TEMPLATE_USAGE_SHARES:
        tr = r["by_template"][tname]
        print(
            f"  {tname:<28} {share:>5.1%} {impl:<38}"
            f" {tr['total_out_tokens']:>8,.0f} {_rng(tr['gwp_g_min'], tr['gwp_g_max']):>14}"
        )
    print()
    _row("Usage-weighted LLM energy", _rng(wt["total_wh_min"], wt["total_wh_max"], "Wh"))
    _row("Usage-weighted LLM CO₂e", _rng(wt["gwp_g_min"], wt["gwp_g_max"], "g"))


if __name__ == "__main__":
    display()
