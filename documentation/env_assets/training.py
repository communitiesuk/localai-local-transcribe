"""Section 10 + Appendix C/D: LLM and ASR training impact (per user, amortised)."""

from utils import (
    ASR_USER_BASE,
    GPT4O_TRAINING_MWH,
    GPT4_TRAINING_MWH,
    LLM_USER_BASE,
    OWSM_GPU_COUNT,
    OWSM_GPU_TDP_W,
    OWSM_PUE,
    OWSM_SERVER_GPU_DRAW_W,
    OWSM_SERVER_NON_GPU_HIGH_W,
    OWSM_SERVER_NON_GPU_LOW_W,
    OWSM_TRAINING_DAYS,
    TRAINING_CARBON_INTENSITY_G_PER_KWH,
    _row,
    _section,
)


def calculate() -> dict:
    # LLM training (Appendix C)
    gpt4_kwh = GPT4_TRAINING_MWH * 1_000
    gpt4o_kwh = GPT4O_TRAINING_MWH * 1_000
    gpt4_per_user_wh = gpt4_kwh / LLM_USER_BASE * 1_000
    gpt4o_per_user_wh = gpt4o_kwh / LLM_USER_BASE * 1_000
    gpt4_co2e_g = gpt4_per_user_wh / 1_000 * TRAINING_CARBON_INTENSITY_G_PER_KWH
    gpt4o_co2e_g = gpt4o_per_user_wh / 1_000 * TRAINING_CARBON_INTENSITY_G_PER_KWH

    # ASR training (Appendix D)
    gpu_energy_kwh = OWSM_GPU_COUNT * OWSM_GPU_TDP_W * 24 * OWSM_TRAINING_DAYS / 1_000
    non_gpu_midpoint_w = (OWSM_SERVER_NON_GPU_LOW_W + OWSM_SERVER_NON_GPU_HIGH_W) / 2
    system_overhead_fraction = non_gpu_midpoint_w / OWSM_SERVER_GPU_DRAW_W
    system_energy_kwh = gpu_energy_kwh * (1 + system_overhead_fraction)
    total_energy_kwh = system_energy_kwh * OWSM_PUE
    asr_per_user_wh = total_energy_kwh / ASR_USER_BASE * 1_000
    asr_co2e_g = asr_per_user_wh / 1_000 * TRAINING_CARBON_INTENSITY_G_PER_KWH

    return {
        "llm": {
            "gpt4_training_kwh": gpt4_kwh,
            "gpt4o_training_kwh": gpt4o_kwh,
            "gpt4_per_user_wh": gpt4_per_user_wh,
            "gpt4o_per_user_wh": gpt4o_per_user_wh,
            "gpt4_co2e_g": gpt4_co2e_g,
            "gpt4o_co2e_g": gpt4o_co2e_g,
            "llm_total_wh": gpt4_per_user_wh + gpt4o_per_user_wh,
            "llm_total_co2e": gpt4_co2e_g + gpt4o_co2e_g,
        },
        "asr": {
            "gpu_energy_kwh": gpu_energy_kwh,
            "non_gpu_midpoint_w": non_gpu_midpoint_w,
            "system_overhead_fraction": system_overhead_fraction,
            "system_energy_kwh": system_energy_kwh,
            "total_energy_kwh": total_energy_kwh,
            "per_user_wh": asr_per_user_wh,
            "co2e_g": asr_co2e_g,
        },
    }


def display() -> None:
    import llm_inference
    import transcription
    from utils import combined_impact, _rng

    r = calculate()
    llm_t = r["llm"]
    asr_t = r["asr"]

    _section("Appendix C: LLM Training Impact (per user, amortised)")
    print("  NOTE: GPT-5.x training costs are not publicly available.")
    print("  GPT-4 / GPT-4o figures below are used as order-of-magnitude proxies.")
    print()
    _row("GPT-4 training total", f"{GPT4_TRAINING_MWH:,} MWh = {llm_t['gpt4_training_kwh']:,.0f} kWh")
    _row(
        "GPT-4 per-user energy",
        f"{llm_t['gpt4_training_kwh']:,.0f} kWh / {LLM_USER_BASE:,}  = {llm_t['gpt4_per_user_wh']:.2f} Wh",
    )
    _row(
        "GPT-4 per-user CO₂e",
        f"{llm_t['gpt4_per_user_wh']:.2f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh"
        f"  = {llm_t['gpt4_co2e_g']:.2f} g",
    )
    print()
    _row("GPT-4o training total", f"{GPT4O_TRAINING_MWH:,} MWh = {llm_t['gpt4o_training_kwh']:,.0f} kWh")
    _row(
        "GPT-4o per-user energy",
        f"{llm_t['gpt4o_training_kwh']:,.0f} kWh / {LLM_USER_BASE:,}  = {llm_t['gpt4o_per_user_wh']:.4f} Wh",
    )
    _row(
        "GPT-4o per-user CO₂e",
        f"{llm_t['gpt4o_per_user_wh']:.4f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh"
        f"  = {llm_t['gpt4o_co2e_g']:.4f} g",
    )
    print()
    _row(
        "LLM combined per-user energy",
        f"{llm_t['gpt4_per_user_wh']:.2f} + {llm_t['gpt4o_per_user_wh']:.4f}  = {llm_t['llm_total_wh']:.2f} Wh",
    )
    _row(
        "LLM combined per-user CO₂e",
        f"{llm_t['gpt4_co2e_g']:.2f} + {llm_t['gpt4o_co2e_g']:.4f}  = {llm_t['llm_total_co2e']:.2f} g",
    )

    _section("Appendix D: ASR Training Impact — OWSM v3 proxy (per user)")
    _row(
        "Tier 1 — GPU energy",
        f"{OWSM_GPU_COUNT} GPUs × {OWSM_GPU_TDP_W}W × 24h × {OWSM_TRAINING_DAYS}d / 1000"
        f"  = {asr_t['gpu_energy_kwh']:,.0f} kWh",
    )
    _row(
        "Non-GPU overhead (midpoint)",
        f"({OWSM_SERVER_NON_GPU_LOW_W}+{OWSM_SERVER_NON_GPU_HIGH_W}) / 2"
        f"  = {asr_t['non_gpu_midpoint_w']:.0f} W"
        f"  →  fraction = {asr_t['system_overhead_fraction']:.4f}",
    )
    _row(
        "Tier 2 — + system overhead",
        f"{asr_t['gpu_energy_kwh']:,.0f} × (1 + {asr_t['system_overhead_fraction']:.4f})"
        f"  = {asr_t['system_energy_kwh']:,.0f} kWh",
    )
    _row(
        "Tier 3 — + PUE",
        f"{asr_t['system_energy_kwh']:,.0f} × {OWSM_PUE}  = {asr_t['total_energy_kwh']:,.0f} kWh",
    )
    _row(
        "Per-user energy",
        f"{asr_t['total_energy_kwh']:,.0f} kWh / {ASR_USER_BASE:,} × 1000  = {asr_t['per_user_wh']:.4f} Wh",
    )
    _row(
        "Per-user CO₂e",
        f"{asr_t['per_user_wh']:.4f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh"
        f"  = {asr_t['co2e_g']:.4f} g",
    )

    # Section 10.2: training vs inference comparison
    system_training_wh = llm_t["llm_total_wh"] + asr_t["per_user_wh"]
    system_training_co2e = llm_t["llm_total_co2e"] + asr_t["co2e_g"]
    asr_r = transcription.calculate()
    llm_r = llm_inference.calculate()
    simple_combined = combined_impact(llm_r["simple_template"], asr_r)

    _section("Section 10.2: Training vs Inference (SimpleTemplate baseline)")
    print("  NOTE: training figures use GPT-4/GPT-4o proxies (GPT-5.x unpublished).")
    _row(
        "System training total per user (proxy)",
        f"{llm_t['llm_total_wh']:.2f} + {asr_t['per_user_wh']:.4f}"
        f"  = {system_training_wh:.2f} Wh  /  {system_training_co2e:.2f} g CO₂e",
    )
    _row(
        "1-hour SimpleTemplate meeting",
        _rng(simple_combined["total_energy_wh_min"], simple_combined["total_energy_wh_max"], "Wh")
        + "  /  "
        + _rng(simple_combined["total_co2e_g_min"], simple_combined["total_co2e_g_max"], "g CO₂e"),
    )
    ratio_mid = simple_combined["total_energy_wh"] / system_training_wh
    _row(
        "Inference / training ratio (midpoint)",
        f"{simple_combined['total_energy_wh']:.2f} / {system_training_wh:.2f}  = {ratio_mid:.2f}×",
    )
    print()


if __name__ == "__main__":
    display()
