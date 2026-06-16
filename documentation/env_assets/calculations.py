"""
Environmental Impact Calculations for Local Transcribe.

Reproduces every calculation from documentation/env-impact.md.
All ASSUMPTIONS are at the top — edit them to explore scenarios.
Every result is derived directly; no pre-computed constant feeds into another step.

Inference energy is computed via EcoLogits 0.10.2 (LCA regression model).
Each API invocation is modelled individually — not aggregated — so that
time-to-first-token (TTFT) is counted once per real network request:

  - Fast invocations use GPT-5-nano  (dense, 5–18.5 B params, TPS=96.1, TTFT=2.29 s)
  - Best invocations use GPT-5.1     (MoE, 300 B total / 30–90 B active, TPS=60.6, TTFT=1.85 s)
  - TPS and TTFT are taken from EcoLogits ModelRepository deployment measurements.
  - Data centre: OpenAI config (PUE, WUE) loaded dynamically from PROVIDER_CONFIG_MAP.
  - Electricity mix for energy calculation: UK (GBR) grid, loaded from ElectricityMixRepository.
  - CO₂e derived as energy × GBR carbon intensity (217 g/kWh).
  - Only OUTPUT tokens drive generation energy; TTFT models input/prefill overhead.
  - Results are reported as min–max ranges reflecting architecture uncertainty.

Run with (from documentation/env_assets/):
    poetry run python calculations.py
Install first: cd documentation/env_assets && poetry install
"""

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

import yaml
from ecologits.electricity_mix_repository import ElectricityMixRepository
from ecologits.impacts.llm import compute_llm_impacts
from ecologits.model_repository import ModelRepository
from ecologits.tracers.utils import PROVIDER_CONFIG_MAP
from ecologits.utils.range_value import RangeValue

# Load assumptions from YAML (all reference/measured values live there).
_cfg = yaml.safe_load((Path(__file__).parent / "assumptions.yaml").read_text())

# Load all grid/datacenter/model data from EcoLogits at import time.
_openai_cfg = PROVIDER_CONFIG_MAP["openai"]
_elec_repo = ElectricityMixRepository.from_json()
_uk_mix = _elec_repo.find_electricity_mix(zone="GBR")
_usa_mix = _elec_repo.find_electricity_mix(zone="USA")
_model_repo = ModelRepository.from_json()
_nano_model = _model_repo.find_model(provider="openai", model_name="gpt-5-nano")
_best_model = _model_repo.find_model(provider="openai", model_name="gpt-5.1")

# =============================================================================
# ASSUMPTIONS — loaded from assumptions.yaml
# =============================================================================

# --- Meeting / transcript ---
TRANSCRIPT_WORDS: int = _cfg["meeting"]["transcript_words"]
NUM_SECTIONS: int = _cfg["meeting"]["num_sections"]
TOKENS_PER_WORD: int = _cfg["meeting"]["tokens_per_word"]

# --- ASR study measurements [15] ---
ASR_STUDY_TOTAL_ENERGY_KWH: float = _cfg["asr_study"]["total_energy_kwh"]
ASR_STUDY_AUDIO_HOURS: int = _cfg["asr_study"]["audio_hours"]
ASR_STUDY_TOTAL_CO2E_G: int = _cfg["asr_study"]["total_co2e_g"]

# --- LLM training proxies [11] ---
GPT4_TRAINING_MWH: int = _cfg["llm_training"]["gpt4_mwh"]
GPT4O_TRAINING_MWH: int = _cfg["llm_training"]["gpt4o_mwh"]
LLM_USER_BASE: int = _cfg["llm_training"]["user_base"]

# --- Template prompt word counts ---
EXEC_SUMMARY_SYSTEM_WORDS: int = _cfg["templates"]["exec_summary_system_words"]
DOCUMENT_PROMPT_FIXED_WORDS: int = _cfg["templates"]["document_prompt_fixed_words"]
USER_TEMPLATE_CONTENT_WORDS: int = _cfg["templates"]["user_template_content_words"]
DOCUMENT_DATE_WORDS: int = _cfg["templates"]["document_date_words"]

# --- OWSM v3 training hardware [19][20][21][22] ---
OWSM_GPU_COUNT: int = _cfg["owsm_training"]["gpu_count"]
OWSM_GPU_TDP_W: int = _cfg["owsm_training"]["gpu_tdp_w"]
OWSM_TRAINING_DAYS: int = _cfg["owsm_training"]["training_days"]
OWSM_SERVER_GPU_DRAW_W: int = _cfg["owsm_training"]["server_gpu_draw_w"]
OWSM_SERVER_NON_GPU_LOW_W: int = _cfg["owsm_training"]["server_non_gpu_low_w"]
OWSM_SERVER_NON_GPU_HIGH_W: int = _cfg["owsm_training"]["server_non_gpu_high_w"]
OWSM_PUE: float = _cfg["owsm_training"]["pue"]
ASR_USER_BASE: int = _cfg["owsm_training"]["user_base"]

# --- Homeworking emission factors [24] ---
HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR: float = _cfg["homeworking"]["office_equipment_kg_co2e_per_hour"]
HOMEWORKING_HEATING_KG_CO2E_PER_HOUR: float = _cfg["homeworking"]["heating_kg_co2e_per_hour"]
HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR: float = _cfg["homeworking"]["total_kg_co2e_per_hour"]
WORKING_HOURS_PER_DAY: int = _cfg["homeworking"]["working_hours_per_day"]

# --- AWS hosting snapshot ---
AWS_APR2026_CO2E_G: int = _cfg["aws"]["apr2026_co2e_g"]

# --- Passenger car [26] ---
CAR_AVG_PETROL_WLTP_GCO2_PER_KM: float = _cfg["car"]["avg_petrol_wltp_gco2_per_km"]
CAR_REAL_WORLD_UPLIFT_FRACTION: float = _cfg["car"]["real_world_uplift_fraction"]

# --- Long-haul economy flight [26] ---
FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE: float = _cfg["flight"]["long_haul_economy_gco2_per_pkm_base"]
FLIGHT_DISTANCE_UPLIFT_FRACTION: float = _cfg["flight"]["distance_uplift_fraction"]
FLIGHT_RF_MULTIPLIER: float = _cfg["flight"]["rf_multiplier"]

# --- Television [28] ---
TV_TYPICAL_WATTAGE: int = _cfg["television"]["typical_wattage"]

# --- UK household energy [27] ---
HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR: int = _cfg["household"]["electricity_kwh_per_year"]
HOUSEHOLD_GAS_KWH_PER_YEAR: int = _cfg["household"]["gas_kwh_per_year"]

# =============================================================================
# DERIVED CONSTANTS — computed from EcoLogits API/library calls
# =============================================================================

# Carbon intensity (loaded from EcoLogits ElectricityMixRepository)
ASR_CARBON_INTENSITY_G_PER_KWH: float = _uk_mix.gwp * 1000   # GBR, ≈217 g/kWh [25]
TRAINING_CARBON_INTENSITY_G_PER_KWH: float = _usa_mix.gwp * 1000  # USA, ≈384 g/kWh [25]
LLM_CARBON_INTENSITY_G_PER_KWH: float = _uk_mix.gwp * 1000   # GBR, used for LLM CO₂e

# LLM models (loaded from EcoLogits ModelRepository)
GPT5_NANO_PARAMS_B: RangeValue = _nano_model.architecture.parameters
GPT5_NANO_TPS: float = _nano_model.deployment.tps
GPT5_NANO_TTFT: float = _nano_model.deployment.ttft

GPT51_TOTAL_B: int = _best_model.architecture.parameters.total
GPT51_ACTIVE_B: RangeValue = _best_model.architecture.parameters.active
GPT51_TPS: float = _best_model.deployment.tps
GPT51_TTFT: float = _best_model.deployment.ttft

# OpenAI data-centre configuration (from EcoLogits PROVIDER_CONFIG_MAP)
OPENAI_PUE: float = _openai_cfg.datacenter_pue
OPENAI_WUE: float = _openai_cfg.datacenter_wue

# UK electricity mix (from EcoLogits ElectricityMixRepository, zone='GBR')
UK_GWP_KG_PER_KWH: float = _uk_mix.gwp
UK_ADPE: float = _uk_mix.adpe
UK_PE: float = _uk_mix.pe
UK_WUE: float = _uk_mix.wue


# =============================================================================
# HELPERS
# =============================================================================


def words_to_tokens(words: float) -> float:
    return words * TOKENS_PER_WORD


def _section(title: str) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print("=" * 62)


def _row(label: str, value: str) -> None:
    print(f"  {label:<44} {value}")


def _rng(lo: float, hi: float, unit: str = "", dp: int = 1) -> str:
    fmt = f".{dp}f"
    return f"{lo:{fmt}}–{hi:{fmt}} {unit}".strip()


# =============================================================================
# LLM ENERGY (EcoLogits) — per-invocation model
# =============================================================================


def _inv(output_words: float, model: str) -> dict:
    """
    Compute EcoLogits impact for a single API invocation.

    Passes deployment TPS and TTFT so that each call's prefill overhead
    is counted individually rather than amortised across all invocations.

    Args:
        output_words: Words generated by this invocation (output only).
        model: 'fast' (GPT-5-nano) or 'best' (GPT-5.1).

    Returns:
        Dict with per-invocation energy (Wh) and GWP (g CO₂eq) min/max ranges,
        plus 'model' and 'out_tokens' for aggregation.
    """
    output_tokens = words_to_tokens(output_words)
    if output_tokens == 0:
        return {
            "model": model,
            "out_tokens": 0.0,
            "wh_min": 0.0,
            "wh_max": 0.0,
            "gwp_g_min": 0.0,
            "gwp_g_max": 0.0,
        }

    if model == "fast":
        active = GPT5_NANO_PARAMS_B  # dense: active == total
        total = GPT5_NANO_PARAMS_B
        tps = GPT5_NANO_TPS
        ttft = GPT5_NANO_TTFT
    else:
        active = GPT51_ACTIVE_B
        total = GPT51_TOTAL_B
        tps = GPT51_TPS
        ttft = GPT51_TTFT

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
        # CO₂e derived as energy × GBR intensity.
        "gwp_g_min": wh_min / 1000 * LLM_CARBON_INTENSITY_G_PER_KWH,
        "gwp_g_max": wh_max / 1000 * LLM_CARBON_INTENSITY_G_PER_KWH,
    }


def _combine(*invocations: dict) -> dict:
    """
    Aggregate per-invocation EcoLogits results into a template-level summary.

    Returns the same structure as the old _llm_result() so all downstream
    reporting code continues to work unchanged.
    """
    fast_tokens = sum(i["out_tokens"] for i in invocations if i["model"] == "fast")
    best_tokens = sum(i["out_tokens"] for i in invocations if i["model"] == "best")

    fast_wh_min = sum(i["wh_min"] for i in invocations if i["model"] == "fast")
    fast_wh_max = sum(i["wh_max"] for i in invocations if i["model"] == "fast")
    best_wh_min = sum(i["wh_min"] for i in invocations if i["model"] == "best")
    best_wh_max = sum(i["wh_max"] for i in invocations if i["model"] == "best")

    wh_min = fast_wh_min + best_wh_min
    wh_max = fast_wh_max + best_wh_max
    gwp_min = sum(i["gwp_g_min"] for i in invocations)
    gwp_max = sum(i["gwp_g_max"] for i in invocations)

    return {
        "fast_out_tokens": fast_tokens,
        "best_out_tokens": best_tokens,
        "total_out_tokens": fast_tokens + best_tokens,
        "fast_wh_min": fast_wh_min,
        "fast_wh_max": fast_wh_max,
        "best_wh_min": best_wh_min,
        "best_wh_max": best_wh_max,
        "total_wh_min": wh_min,
        "total_wh_max": wh_max,
        "total_wh": (wh_min + wh_max) / 2,  # midpoint — for weighted aggregation
        "gwp_g_min": gwp_min,
        "gwp_g_max": gwp_max,
        "co2e_g": (gwp_min + gwp_max) / 2,  # midpoint — for weighted aggregation
    }


# =============================================================================
# SECTION 6: TRANSCRIPTION IMPACT (1-hour meeting)
# =============================================================================


def transcription_impact() -> dict:
    # Per-hour energy from study measurement
    energy_wh = (ASR_STUDY_TOTAL_ENERGY_KWH * 1_000) / ASR_STUDY_AUDIO_HOURS

    # CO₂e as reported by the study (uses study's implied carbon intensity)
    co2e_g_study = ASR_STUDY_TOTAL_CO2E_G / ASR_STUDY_AUDIO_HOURS

    # CO₂e recalculated with GBR intensity for consistent combined-total percentages
    co2e_g_gbr = (energy_wh / 1_000) * ASR_CARBON_INTENSITY_G_PER_KWH

    return {
        "energy_wh": energy_wh,
        "co2e_g_study": co2e_g_study,
        "co2e_g_eu27": co2e_g_gbr,
    }


# =============================================================================
# SECTION 7: LLM TOKEN USAGE AND ENERGY (Appendix B)
# =============================================================================


def simple_template(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.2 — SimpleTemplate: General / Care Assessment / Care Assessment V2 (6 invocations).

    Each API call is modelled individually so TTFT is counted per request.
    Only OUTPUT words drive the energy formula; input tokens are covered by TTFT.

    FAST (GPT-5-nano):
      1. Speaker ID    (generate_speaker_predictions.py): out ≈ 40 words
      2. Title         (meeting_title.j2):                out ≈ 10 words
      5. extract_claims (extract_claims.j2):              out ≈ 0.1X words
      6. cite_claims   (cite_claims.j2):                  out ≈ 0.5X words

    BEST (GPT-5.1):
      3. Minutes       (general.j2 + transcript.j2):      out ≈ 0.5X words
      4. Hallucination (hallucination_detection.j2):      out ≈ 80 words
    """
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.5 * x, "best"),  # 3. minutes
        _inv(80, "best"),  # 4. hallucination check
        _inv(0.1 * x, "fast"),  # 5. extract_claims
        _inv(0.5 * x, "fast"),  # 6. cite_claims
    )


def section_template(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    """
    B.3 — SectionTemplate: Cabinet / Planning Committee (5 + 2Y invocations).

    Section generation and hallucination checks are each separate API calls,
    so Y sections → Y individual EcoLogits calls, each charged its own TTFT.

    FAST (GPT-5-nano):
      1. Speaker ID         out ≈ 40 words
      2. Title              out ≈ 10 words
      3. Section detection  (sections_from_transcript.j2): out ≈ 2Y words
      4+Y+1. extract_claims out ≈ 0.06X words
      5+Y+1. cite_claims    out ≈ 0.3X words

    BEST (GPT-5.1) — Y+Y calls:
      4…4+Y-1. Section content (one call per section): out ≈ (0.3X / Y) words each
      5…5+Y-1. Hallucination check per section:        out ≈ 80 words each
    """
    section_words = 0.3 * x / y  # per-section output
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
    """
    B.4 — Delivery Template (6 invocations: 4 FAST + 2 BEST).

    FAST (GPT-5-nano):
      1. Speaker ID:       out ≈ 40 words
      2. Title:            out ≈ 10 words
      5. extract_claims:   out ≈ 0.08X words
      6. cite_claims:      out ≈ 0.4X words

    BEST (GPT-5.1):
      3. Sections + Actions + Attendees: out ≈ 0.4X + 30 words
      4. Hallucination:                  out ≈ 80 words
    """
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.4 * x + 30, "best"),  # 3. sections + actions + attendees
        _inv(80, "best"),  # 4. hallucination check
        _inv(0.08 * x, "fast"),  # 5. extract_claims
        _inv(0.4 * x, "fast"),  # 6. cite_claims
    )


def basic_minutes(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.5 — Basic Minutes fallback (4 FAST-only invocations).

    FAST (GPT-5-nano):
      1. Speaker ID:    out ≈ 40 words
      2. Title:         out ≈ 10 words
      3. Basic summary: out ≈ 0.3X words
      4. Hallucination: out ≈ 80 words
    """
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.3 * x, "fast"),  # 3. summary
        _inv(80, "fast"),  # 4. hallucination check
    )


def executive_summary(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.2a — Short 'n' Sweet / ExecutiveSummary (4 invocations, no citations).

    FAST (GPT-5-nano):
      1. Speaker ID: out ≈ 40 words
      2. Title:      out ≈ 10 words

    BEST (GPT-5.1):
      3. Minutes (executive_summary.j2): out ≈ 0.3X words
      4. Hallucination:                  out ≈ 80 words
    """
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.3 * x, "best"),  # 3. minutes
        _inv(80, "best"),  # 4. hallucination check
    )


def user_template_document(x: float = TRANSCRIPT_WORDS) -> dict:
    """
    B.6.1 — UserTemplate (DOCUMENT type): 4 invocations (2 FAST + 2 BEST).

    FAST (GPT-5-nano):
      1. Speaker ID: out ≈ 40 words
      2. Title:      out ≈ 10 words

    BEST (GPT-5.1):
      3. Document output: out ≈ 0.5X words
      4. Hallucination:   out ≈ 80 words
    """
    return _combine(
        _inv(40, "fast"),  # 1. speaker_id
        _inv(10, "fast"),  # 2. title
        _inv(0.5 * x, "best"),  # 3. document generation
        _inv(80, "best"),  # 4. hallucination check
    )


# =============================================================================
# APPENDIX F.2: USAGE-WEIGHTED IMPACT
# Production usage shares (December 2024 – May 2026, Appendix F.1)
# =============================================================================

# (template_name, production_share, implementation) — loaded from assumptions.yaml
TEMPLATE_USAGE_SHARES: list[tuple[str, float, str]] = [
    (row["name"], row["share"], row["implementation"])
    for row in _cfg["template_usage_shares"]
]


def _template_result(name: str, x: float, y: int = NUM_SECTIONS) -> dict:
    """Map a production template name to its calculated LLM result."""
    mapping: dict[str, dict] = {
        "General": simple_template(x),
        "Delivery": delivery_template(x),
        "Short 'n' Sweet": executive_summary(x),
        "User generated": user_template_document(x),
        "Cabinet": section_template(x, y),
        "Care Assessment": simple_template(x),
        "Planning Committee": section_template(x, y),
        "Care Assessment V2": simple_template(x),
    }
    return mapping[name]


def usage_weighted_impact(x: float = TRANSCRIPT_WORDS, y: int = NUM_SECTIONS) -> dict:
    """
    F.2.3 — Compute usage-weighted average LLM impact across all production templates.
    """
    wt_out_tokens = 0.0
    wt_wh_min = wt_wh_max = 0.0
    wt_gwp_min = wt_gwp_max = 0.0

    for name, share, _ in TEMPLATE_USAGE_SHARES:
        r = _template_result(name, x, y)
        wt_out_tokens += share * r["total_out_tokens"]
        wt_wh_min += share * r["total_wh_min"]
        wt_wh_max += share * r["total_wh_max"]
        wt_gwp_min += share * r["gwp_g_min"]
        wt_gwp_max += share * r["gwp_g_max"]

    return {
        "total_out_tokens": wt_out_tokens,
        "total_wh_min": wt_wh_min,
        "total_wh_max": wt_wh_max,
        "total_wh": (wt_wh_min + wt_wh_max) / 2,  # midpoint
        "gwp_g_min": wt_gwp_min,
        "gwp_g_max": wt_gwp_max,
        "co2e_g": (wt_gwp_min + wt_gwp_max) / 2,  # midpoint
    }


# =============================================================================
# SECTION 8: COMBINED IMPACT (Transcription + LLM)
# =============================================================================


def combined_impact(llm: dict, asr: dict) -> dict:
    energy_min = llm["total_wh_min"] + asr["energy_wh"]
    energy_max = llm["total_wh_max"] + asr["energy_wh"]
    co2e_min = llm["gwp_g_min"] + asr["co2e_g_eu27"]
    co2e_max = llm["gwp_g_max"] + asr["co2e_g_eu27"]
    co2e_mid = (co2e_min + co2e_max) / 2
    asr_pct = 100 * asr["co2e_g_eu27"] / co2e_mid if co2e_mid else 0
    llm_pct = 100 * llm["co2e_g"] / co2e_mid if co2e_mid else 0
    return {
        "total_energy_wh_min": energy_min,
        "total_energy_wh_max": energy_max,
        "total_energy_wh": (energy_min + energy_max) / 2,
        "total_co2e_g_min": co2e_min,
        "total_co2e_g_max": co2e_max,
        "total_co2e_g": co2e_mid,
        "asr_pct": asr_pct,
        "llm_pct": llm_pct,
    }


# =============================================================================
# SECTION 10 / APPENDIX C: LLM TRAINING IMPACT (per user)
# =============================================================================


def llm_training_impact() -> dict:
    gpt4_training_kwh = GPT4_TRAINING_MWH * 1_000
    gpt4o_training_kwh = GPT4O_TRAINING_MWH * 1_000

    gpt4_per_user_kwh = gpt4_training_kwh / LLM_USER_BASE
    gpt4o_per_user_kwh = gpt4o_training_kwh / LLM_USER_BASE

    gpt4_per_user_wh = gpt4_per_user_kwh * 1_000
    gpt4o_per_user_wh = gpt4o_per_user_kwh * 1_000

    gpt4_co2e_g = gpt4_per_user_kwh * TRAINING_CARBON_INTENSITY_G_PER_KWH
    gpt4o_co2e_g = gpt4o_per_user_kwh * TRAINING_CARBON_INTENSITY_G_PER_KWH

    return {
        "gpt4_training_kwh": gpt4_training_kwh,
        "gpt4o_training_kwh": gpt4o_training_kwh,
        "gpt4_per_user_wh": gpt4_per_user_wh,
        "gpt4o_per_user_wh": gpt4o_per_user_wh,
        "gpt4_co2e_g": gpt4_co2e_g,
        "gpt4o_co2e_g": gpt4o_co2e_g,
        "llm_total_wh": gpt4_per_user_wh + gpt4o_per_user_wh,
        "llm_total_co2e": gpt4_co2e_g + gpt4o_co2e_g,
    }


# =============================================================================
# APPENDIX D: ASR (OWSM v3) TRAINING IMPACT
# =============================================================================


def asr_training_impact() -> dict:
    gpu_energy_kwh = OWSM_GPU_COUNT * OWSM_GPU_TDP_W * 24 * OWSM_TRAINING_DAYS / 1_000
    non_gpu_midpoint_w = (OWSM_SERVER_NON_GPU_LOW_W + OWSM_SERVER_NON_GPU_HIGH_W) / 2
    system_overhead_fraction = non_gpu_midpoint_w / OWSM_SERVER_GPU_DRAW_W
    system_energy_kwh = gpu_energy_kwh * (1 + system_overhead_fraction)
    total_energy_kwh = system_energy_kwh * OWSM_PUE
    per_user_kwh = total_energy_kwh / ASR_USER_BASE
    per_user_wh = per_user_kwh * 1_000
    co2e_g = per_user_kwh * TRAINING_CARBON_INTENSITY_G_PER_KWH
    return {
        "gpu_energy_kwh": gpu_energy_kwh,
        "non_gpu_midpoint_w": non_gpu_midpoint_w,
        "system_overhead_fraction": system_overhead_fraction,
        "system_energy_kwh": system_energy_kwh,
        "total_energy_kwh": total_energy_kwh,
        "per_user_wh": per_user_wh,
        "co2e_g": co2e_g,
    }


# =============================================================================
# APPENDIX HW: HOMEWORKING DISPLACEMENT
# =============================================================================


def homeworking_displacement(co2e_g: float) -> dict:
    """Express a CO₂e quantity as the equivalent duration of one person working from home."""
    hw_g_per_hour = HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR * 1_000
    hours = co2e_g / hw_g_per_hour
    return {
        "hw_g_per_hour": hw_g_per_hour,
        "hours": hours,
        "minutes": hours * 60,
        "seconds": hours * 3_600,
        "working_days": hours / WORKING_HOURS_PER_DAY,
    }


def car_displacement(co2e_g: float) -> dict:
    """Express a CO₂e quantity as the equivalent distance driven in an average petrol car."""
    g_per_km = CAR_AVG_PETROL_WLTP_GCO2_PER_KM * (1 + CAR_REAL_WORLD_UPLIFT_FRACTION)
    km = co2e_g / g_per_km
    return {
        "g_per_km": g_per_km,
        "km": km,
        "metres": km * 1_000,
    }


def flight_displacement(co2e_g: float) -> dict:
    """Express a CO₂e quantity as the equivalent passenger-distance on a long-haul economy flight."""
    g_per_pkm = (
        FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE * (1 + FLIGHT_DISTANCE_UPLIFT_FRACTION) * FLIGHT_RF_MULTIPLIER
    )
    pkm = co2e_g / g_per_pkm
    return {
        "g_per_pkm": g_per_pkm,
        "pkm": pkm,
        "metres": pkm * 1_000,
    }


def tv_displacement(energy_wh: float) -> dict:
    """Express an energy quantity as the equivalent duration of watching television."""
    minutes = energy_wh * 60 / TV_TYPICAL_WATTAGE
    return {
        "wattage": TV_TYPICAL_WATTAGE,
        "minutes": minutes,
    }


def tv_co2e_time(co2e_g: float) -> dict:
    """Express a CO₂e quantity as equivalent TV viewing time.

    Converts TV energy to CO₂e using UK grid intensity, then inverts.
    Units check:
      TV_TYPICAL_WATTAGE [W] × LLM_CARBON_INTENSITY_G_PER_KWH [g/kWh]
        / 1000 [Wh/kWh] / 60 [min/h]  = g CO₂e/min  (W × g/Wh / min·h⁻¹ = g/min ✓)
    """
    g_per_min = TV_TYPICAL_WATTAGE * LLM_CARBON_INTENSITY_G_PER_KWH / 1_000 / 60
    return {
        "g_per_min": g_per_min,
        "minutes": co2e_g / g_per_min,
        "hours": co2e_g / g_per_min / 60,
    }


def household_co2e_time(co2e_g: float) -> dict:
    """Express a CO₂e quantity as equivalent household energy consumption time.

    Converts average household power to CO₂e rate using UK grid intensity, then inverts.
    Units check:
      avg_w [W] × LLM_CARBON_INTENSITY_G_PER_KWH [g/kWh]
        / 1000 [Wh/kWh] / 3600 [s/h]  = g CO₂e/s  (W × g/Wh / s·h⁻¹ = g/s ✓)
    """
    daily_wh = (HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR + HOUSEHOLD_GAS_KWH_PER_YEAR) / 365 * 1_000
    avg_w = daily_wh / 24
    g_per_s = avg_w * LLM_CARBON_INTENSITY_G_PER_KWH / 1_000 / 3_600
    seconds = co2e_g / g_per_s
    return {
        "avg_w": avg_w,
        "g_per_s": g_per_s,
        "seconds": seconds,
        "minutes": seconds / 60,
        "hours": seconds / 3_600,
        "days": seconds / 86_400,
    }


def household_energy_fraction(energy_wh: float) -> dict:
    """Express an energy quantity as a fraction of a UK medium household's daily energy use.

    Units check:
      daily_wh [Wh/day] / 24 [h/day] = avg_w [W]
      energy_wh [Wh] / avg_w [W]      = hours [h]   (Wh / W = h ✓)
      hours × 60                       = minutes
      hours × 3600                     = seconds
    """
    daily_wh = (HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR + HOUSEHOLD_GAS_KWH_PER_YEAR) / 365 * 1_000
    avg_w = daily_wh / 24
    hours = energy_wh / avg_w
    return {
        "daily_wh": daily_wh,
        "avg_w": avg_w,
        "fraction": energy_wh / daily_wh,
        "percent": energy_wh / daily_wh * 100,
        "hours": hours,
        "minutes": hours * 60,
        "seconds": hours * 3_600,
    }


# =============================================================================
# REPORTING
# =============================================================================


def print_results() -> None:
    asr = transcription_impact()
    st = simple_template()
    sec = section_template()
    dv = delivery_template()
    bm = basic_minutes()
    es = executive_summary()
    utd = user_template_document()
    llm_t = llm_training_impact()
    asr_t = asr_training_impact()
    wt = usage_weighted_impact()

    print("\nENVIRONMENTAL IMPACT ASSESSMENT — Local Transcribe")
    print(
        f"Assumptions: X={TRANSCRIPT_WORDS:,} words  |  Y={NUM_SECTIONS} sections  |  " f"{TOKENS_PER_WORD} tokens/word"
    )
    print(
        f"Models: fast=GPT-5-nano ({GPT5_NANO_PARAMS_B.min}–{GPT5_NANO_PARAMS_B.max}B dense)  |  "
        f"best=GPT-5.1 ({GPT51_ACTIVE_B.min}–{GPT51_ACTIVE_B.max}B active / {GPT51_TOTAL_B}B total MoE)"
    )
    print(
        f"EcoLogits [25]: OpenAI DC (PUE {OPENAI_PUE})  |  "
        f"UK (GBR) grid ({UK_GWP_KG_PER_KWH*1000:.0f} g CO₂eq/kWh)  |  "
        f"LLM CO₂e = energy × {LLM_CARBON_INTENSITY_G_PER_KWH:.0f} g/kWh (GBR)"
    )

    # ── Section 6: Transcription ──────────────────────────────────────────────
    _section("Section 6: Transcription (1-hour meeting)")
    _row("Source: total energy over study", f"{ASR_STUDY_TOTAL_ENERGY_KWH} kWh / {ASR_STUDY_AUDIO_HOURS} hours")
    _row(
        "Energy per hour",
        f"{ASR_STUDY_TOTAL_ENERGY_KWH * 1000} Wh / {ASR_STUDY_AUDIO_HOURS} h"
        f"  = {asr['energy_wh']:.2f} Wh  ({asr['energy_wh'] / 1000:.4f} kWh)",
    )
    _row(
        "CO₂e (study carbon intensity)",
        f"{ASR_STUDY_TOTAL_CO2E_G} g / {ASR_STUDY_AUDIO_HOURS} h" f"  = {asr['co2e_g_study']:.2f} g",
    )
    _row(
        "CO₂e (GBR, used in combined totals)",
        f"{asr['energy_wh']:.2f} Wh × {ASR_CARBON_INTENSITY_G_PER_KWH:.1f} g/kWh / 1000"
        f"  = {asr['co2e_g_eu27']:.2f} g",
    )

    # ── Section 7: LLM per template ──────────────────────────────────────────
    templates = [
        ("Section 7.1: SimpleTemplate", st, "6"),
        (f"Section 7.2: SectionTemplate Y={NUM_SECTIONS}", sec, f"5+2×{NUM_SECTIONS}={5 + 2 * NUM_SECTIONS}"),
        ("Section 7.3: Delivery Template", dv, "6"),
        ("Section 7.4: Basic Minutes (fallback)", bm, "4"),
    ]

    for title, r, inv in templates:
        _section(f"{title}  [{inv} invocations]")
        _row("GPT-5-nano (fast) output tokens", f"{r['fast_out_tokens']:,.0f}")
        _row("GPT-5.1 (best) output tokens", f"{r['best_out_tokens']:,.0f}")
        _row("Total output tokens", f"{r['total_out_tokens']:,.0f}")
        _row("GPT-5-nano energy", _rng(r["fast_wh_min"], r["fast_wh_max"], "Wh"))
        _row("GPT-5.1 energy", _rng(r["best_wh_min"], r["best_wh_max"], "Wh"))
        _row(
            "Total LLM energy",
            f"{_rng(r['total_wh_min'], r['total_wh_max'], 'Wh')}"
            f"  ({_rng(r['total_wh_min']/1000, r['total_wh_max']/1000, 'kWh', dp=4)})",
        )
        _row("CO₂e (energy × GBR 217 g/kWh)", _rng(r["gwp_g_min"], r["gwp_g_max"], "g"))

    # ── Section 7.6: Template comparison ─────────────────────────────────────
    _section("Section 7.6: Template Comparison Summary")
    print(f"  {'Template':<34} {'Invocations':>11} {'Out Tokens':>10} {'Energy (Wh)':>20} {'CO₂e (g)':>16}")
    print(f"  {'-'*34} {'-'*11} {'-'*10} {'-'*20} {'-'*16}")
    rows = [
        ("Basic Minutes", "4", bm),
        ("Short 'n' Sweet (no citations)", "4", es),
        ("UserTemplate DOCUMENT", "4", utd),
        ("Delivery", "6", dv),
        ("SimpleTemplate", "6", st),
        (f"SectionTemplate Y={NUM_SECTIONS}", f"5+2×{NUM_SECTIONS}={5 + 2 * NUM_SECTIONS}", sec),
    ]
    for name, inv, r in rows:
        e_str = _rng(r["total_wh_min"], r["total_wh_max"])
        c_str = _rng(r["gwp_g_min"], r["gwp_g_max"])
        print(f"  {name:<34} {inv:>11} {r['total_out_tokens']:>10,.0f}" f" {e_str:>20} {c_str:>16}")

    # ── Section 8: Combined impact ────────────────────────────────────────────
    _section("Section 8: Combined Impact per 1-Hour Meeting")
    print("  (ASR CO₂e at GBR 217 g/kWh; LLM CO₂e at GBR 217 g/kWh; energy via EcoLogits [25])\n")
    print(f"  {'Template':<30} {'Energy (Wh)':>20} {'CO₂e (g)':>20} {'ASR%':>6} {'LLM%':>6}")
    print(f"  {'-'*30} {'-'*20} {'-'*20} {'-'*6} {'-'*6}")
    for name, _, r in rows:
        c = combined_impact(r, asr)
        e_str = _rng(c["total_energy_wh_min"], c["total_energy_wh_max"])
        co_str = _rng(c["total_co2e_g_min"], c["total_co2e_g_max"])
        print(f"  {name:<30} {e_str:>20} {co_str:>20}" f" {c['asr_pct']:>5.1f}% {c['llm_pct']:>5.1f}%")

    # ── Appendix F.2: Usage-weighted impact ──────────────────────────────────
    _section("Appendix F.2: Usage-Weighted Impact (production shares, Dec 2024–May 2026)")
    print(f"  {'Template':<28} {'Share':>6} {'Impl.':<38} {'Out Tok':>8} {'CO₂e (g)':>14}")
    print(f"  {'-'*28} {'-'*6} {'-'*38} {'-'*8} {'-'*14}")
    for tname, share, impl in TEMPLATE_USAGE_SHARES:
        r = _template_result(tname, TRANSCRIPT_WORDS)
        c_str = _rng(r["gwp_g_min"], r["gwp_g_max"])
        print(f"  {tname:<28} {share:>5.1%} {impl:<38} {r['total_out_tokens']:>8,.0f} {c_str:>14}")
    print()
    wt_combined = combined_impact(wt, asr)
    _row("Usage-weighted LLM energy", _rng(wt["total_wh_min"], wt["total_wh_max"], "Wh"))
    _row("Usage-weighted LLM CO₂e", _rng(wt["gwp_g_min"], wt["gwp_g_max"], "g"))
    _row("+ Transcription (GBR)", f"{asr['energy_wh']:.1f} Wh  /  {asr['co2e_g_eu27']:.1f} g")
    _row(
        "Usage-weighted TOTAL energy",
        _rng(wt_combined["total_energy_wh_min"], wt_combined["total_energy_wh_max"], "Wh")
        + f"  ({_rng(wt_combined['total_energy_wh_min']/1000, wt_combined['total_energy_wh_max']/1000, 'kWh', dp=4)})",
    )
    _row("Usage-weighted TOTAL CO₂e", _rng(wt_combined["total_co2e_g_min"], wt_combined["total_co2e_g_max"], "g"))

    # ── Appendix C: LLM training ──────────────────────────────────────────────
    _section("Appendix C: LLM Training Impact (per user, amortised)")
    print("  NOTE: GPT-5.x training costs are not publicly available.")
    print("  GPT-4 / GPT-4o figures below are used as order-of-magnitude proxies.")
    print()
    _row("GPT-4 training total", f"{GPT4_TRAINING_MWH:,} MWh = {llm_t['gpt4_training_kwh']:,.0f} kWh")
    _row(
        "GPT-4 per-user energy",
        f"{llm_t['gpt4_training_kwh']:,.0f} kWh / {LLM_USER_BASE:,}" f"  = {llm_t['gpt4_per_user_wh']:.2f} Wh",
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
        f"{llm_t['gpt4o_training_kwh']:,.0f} kWh / {LLM_USER_BASE:,}" f"  = {llm_t['gpt4o_per_user_wh']:.4f} Wh",
    )
    _row(
        "GPT-4o per-user CO₂e",
        f"{llm_t['gpt4o_per_user_wh']:.4f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh"
        f"  = {llm_t['gpt4o_co2e_g']:.4f} g",
    )
    print()
    _row(
        "LLM combined per-user energy",
        f"{llm_t['gpt4_per_user_wh']:.2f} + {llm_t['gpt4o_per_user_wh']:.4f}" f"  = {llm_t['llm_total_wh']:.2f} Wh",
    )
    _row(
        "LLM combined per-user CO₂e",
        f"{llm_t['gpt4_co2e_g']:.2f} + {llm_t['gpt4o_co2e_g']:.4f}" f"  = {llm_t['llm_total_co2e']:.2f} g",
    )

    # ── Appendix D: OWSM ASR training ─────────────────────────────────────────
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
        f"{asr_t['system_energy_kwh']:,.0f} × {OWSM_PUE}" f"  = {asr_t['total_energy_kwh']:,.0f} kWh",
    )
    _row(
        "Per-user energy",
        f"{asr_t['total_energy_kwh']:,.0f} kWh / {ASR_USER_BASE:,} × 1000" f"  = {asr_t['per_user_wh']:.4f} Wh",
    )
    _row(
        "Per-user CO₂e",
        f"{asr_t['per_user_wh']:.4f} Wh / 1000 × {TRAINING_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh"
        f"  = {asr_t['co2e_g']:.4f} g",
    )

    # ── Section 10.2: Training vs inference ──────────────────────────────────
    system_training_wh = llm_t["llm_total_wh"] + asr_t["per_user_wh"]
    system_training_co2e = llm_t["llm_total_co2e"] + asr_t["co2e_g"]
    simple_combined = combined_impact(st, asr)

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
        + f"  /  "
        + _rng(simple_combined["total_co2e_g_min"], simple_combined["total_co2e_g_max"], "g CO₂e"),
    )
    ratio_mid = simple_combined["total_energy_wh"] / system_training_wh
    _row(
        "Inference / training ratio (midpoint)",
        f"{simple_combined['total_energy_wh']:.2f} / {system_training_wh:.2f}" f"  = {ratio_mid:.2f}×",
    )
    print()

    # ── Appendix HW: Homeworking displacement ────────────────────────────────
    hw_wt_min = homeworking_displacement(wt_combined["total_co2e_g_min"])
    hw_wt_max = homeworking_displacement(wt_combined["total_co2e_g_max"])
    hw_st_min = homeworking_displacement(simple_combined["total_co2e_g_min"])
    hw_st_max = homeworking_displacement(simple_combined["total_co2e_g_max"])

    _section("Appendix HW: Homeworking Displacement  [UK GHG CF 2025]")
    print("  Source: UK Government GHG Conversion Factors 2025 (DESNZ/DEFRA)")
    print("  https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025")
    print("  Category: Homeworking (office equipment + heating), per FTE working hour, Scope 1+2.")
    print()
    _row("Office equipment", f"{HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    _row("Heating", f"{HOMEWORKING_HEATING_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    _row("Combined (homeworking total)", f"{HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    heating_pct = HOMEWORKING_HEATING_KG_CO2E_PER_HOUR / HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR * 100
    print()
    print("  Question: how long must one homeworker work to emit the same CO₂e as")
    print("  the AI processing for one 1-hour meeting?")
    print()
    _row(
        "Usage-weighted meeting CO₂e",
        _rng(wt_combined["total_co2e_g_min"], wt_combined["total_co2e_g_max"], "g CO₂e"),
    )
    _row(
        "≡ homeworking time",
        f"{_rng(hw_wt_min['seconds'], hw_wt_max['seconds'], 's')}"
        f"  ({_rng(hw_wt_min['minutes'], hw_wt_max['minutes'], 'min')})",
    )
    print()
    _row(
        "SimpleTemplate meeting CO₂e",
        _rng(simple_combined["total_co2e_g_min"], simple_combined["total_co2e_g_max"], "g CO₂e"),
    )
    _row(
        "≡ homeworking time",
        f"{_rng(hw_st_min['seconds'], hw_st_max['seconds'], 's')}"
        f"  ({_rng(hw_st_min['minutes'], hw_st_max['minutes'], 'min')})",
    )
    print()
    wt_sec_mid = (hw_wt_min["seconds"] + hw_wt_max["seconds"]) / 2
    print(f"  → Processing one 1-hour meeting through Local Transcribe emits the same CO₂e")
    print(f"    as ~{wt_sec_mid:.0f} seconds of a single person working from home")
    print(f"    (usage-weighted midpoint, homeworking rate = {HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e/h).")
    print(f"  → Heating accounts for {heating_pct:.0f}% of the homeworking factor.")
    print()

    # ── Appendix HW.2: Additional activity comparisons ───────────────────────
    car_wt_min = car_displacement(wt_combined["total_co2e_g_min"])
    car_wt_max = car_displacement(wt_combined["total_co2e_g_max"])
    flight_wt_min = flight_displacement(wt_combined["total_co2e_g_min"])
    flight_wt_max = flight_displacement(wt_combined["total_co2e_g_max"])
    tv_wt_min = tv_displacement(wt_combined["total_energy_wh_min"])
    tv_wt_max = tv_displacement(wt_combined["total_energy_wh_max"])
    hh_wt_min = household_energy_fraction(wt_combined["total_energy_wh_min"])
    hh_wt_max = household_energy_fraction(wt_combined["total_energy_wh_max"])

    _section("Appendix HW.2: Activity Comparisons [26][27][28]")
    print("  Car and flight use a CO₂e basis; TV and household use an energy basis.")
    print()
    car_g_per_km = CAR_AVG_PETROL_WLTP_GCO2_PER_KM * (1 + CAR_REAL_WORLD_UPLIFT_FRACTION)
    _row(
        "Car real-world factor (avg petrol, Scope 1)",
        f"{CAR_AVG_PETROL_WLTP_GCO2_PER_KM} × (1+{CAR_REAL_WORLD_UPLIFT_FRACTION})"
        f"  = {car_g_per_km:.1f} g CO₂/km  [26]",
    )
    _row(
        "Usage-weighted CO₂e → petrol car",
        f"{_rng(wt_combined['total_co2e_g_min'], wt_combined['total_co2e_g_max'], 'g')}"
        f"  →  {_rng(car_wt_min['metres'], car_wt_max['metres'], 'm')}",
    )
    print()
    flight_g_per_pkm = (
        FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE * (1 + FLIGHT_DISTANCE_UPLIFT_FRACTION) * FLIGHT_RF_MULTIPLIER
    )
    _row(
        "Flight factor (long-haul economy, incl. RF)",
        f"{FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE} × 1.08 × {FLIGHT_RF_MULTIPLIER}"
        f"  = {flight_g_per_pkm:.1f} g CO₂e/pkm  [26]",
    )
    _row(
        "Usage-weighted CO₂e → long-haul flight",
        f"{_rng(wt_combined['total_co2e_g_min'], wt_combined['total_co2e_g_max'], 'g')}"
        f"  →  {_rng(flight_wt_min['metres'], flight_wt_max['metres'], 'm')}",
    )
    print()
    hh_daily_wh = (HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR + HOUSEHOLD_GAS_KWH_PER_YEAR) / 365 * 1_000
    _row(
        "Household daily energy (2,700+11,500 kWh/yr ÷ 365)",
        f"{hh_daily_wh:,.0f} Wh/day  [27]",
    )
    _row(
        "Average household power (38,904 Wh/day ÷ 24 h)",
        f"{hh_daily_wh / 24:,.0f} W  (Wh/day ÷ h/day = W ✓)",
    )
    _row(
        "Usage-weighted energy → household time",
        f"{_rng(wt_combined['total_energy_wh_min'], wt_combined['total_energy_wh_max'], 'Wh')}"
        f"  →  {_rng(hh_wt_min['seconds'], hh_wt_max['seconds'], 's')}  ({_rng(hh_wt_min['percent'], hh_wt_max['percent'], '%', dp=3)})",
    )
    print()
    _row('TV typical power (43–55" LED, indicative)  [28]', f"{TV_TYPICAL_WATTAGE} W")
    _row(
        "Usage-weighted energy → TV viewing",
        f"{_rng(wt_combined['total_energy_wh_min'], wt_combined['total_energy_wh_max'], 'Wh')}"
        f"  →  {_rng(tv_wt_min['minutes'], tv_wt_max['minutes'], 'min')}",
    )
    print()
    car_m_mid = (car_wt_min["metres"] + car_wt_max["metres"]) / 2
    flight_m_mid = (flight_wt_min["metres"] + flight_wt_max["metres"]) / 2
    tv_min_mid = (tv_wt_min["minutes"] + tv_wt_max["minutes"]) / 2
    hh_sec_mid = (hh_wt_min["seconds"] + hh_wt_max["seconds"]) / 2
    print(f"  → Driving ~{car_m_mid:.0f} m in a petrol car  |  long-haul flight ~{flight_m_mid:.0f} m")
    print(f"    Watching TV ~{tv_min_mid:.0f} min  |  ~{hh_sec_mid:.0f} s of household energy consumption")
    print()

    # ── Appendix HW.3: Cross-layer comparison ────────────────────────────────
    # All CO₂e-based (car, flight, homeworking). Energy-based (TV, household)
    # is shown only for inference where EcoLogits gives real Wh figures; AWS
    # billing reports market-based CO₂e without a reliable Wh equivalent.
    training_co2e = llm_t["llm_total_co2e"] + asr_t["co2e_g"]
    training_wh = llm_t["llm_total_wh"] + asr_t["per_user_wh"]

    c_train = car_displacement(training_co2e)
    f_train = flight_displacement(training_co2e)
    hw_train = homeworking_displacement(training_co2e)
    tv_train = tv_displacement(training_wh)
    hh_train = household_energy_fraction(training_wh)

    c_meet = car_displacement(wt_combined["total_co2e_g"])
    f_meet = flight_displacement(wt_combined["total_co2e_g"])
    hw_meet = homeworking_displacement(wt_combined["total_co2e_g"])

    c_aws = car_displacement(AWS_APR2026_CO2E_G)
    f_aws = flight_displacement(AWS_APR2026_CO2E_G)
    hw_aws = homeworking_displacement(AWS_APR2026_CO2E_G)

    # All comparisons on a unified CO₂e basis.
    # TV and household are converted: wattage × UK grid intensity → g CO₂e/min or /s.
    tv_train_co2e = tv_co2e_time(training_co2e)
    hh_train_co2e = household_co2e_time(training_co2e)
    tv_meet_co2e = tv_co2e_time(wt_combined["total_co2e_g"])
    hh_meet_co2e = household_co2e_time(wt_combined["total_co2e_g"])
    tv_aws_co2e = tv_co2e_time(AWS_APR2026_CO2E_G)
    hh_aws_co2e = household_co2e_time(AWS_APR2026_CO2E_G)

    _section("Appendix HW.3: Cross-Layer Activity Comparison (unified CO₂e basis)")
    print("  All columns use CO₂e. TV/household: wattage × UK grid intensity (217 g/kWh).")
    print()
    w = 42
    print(
        f"  {'Cost layer':<{w}} {'CO₂e':>8}  {'Car':>8}  {'Flight':>10}"
        f"  {'Homeworking':>13}  {'TV (100 W)':>12}  {'Household':>12}"
    )
    print(f"  {'-'*w} {'-'*8}  {'-'*8}  {'-'*10}  {'-'*13}  {'-'*12}  {'-'*12}")
    print(
        f"  {'LLM+ASR training, per user (proxy)':<{w}}"
        f" {training_co2e:>6.1f} g"
        f"  {c_train['metres']:>6.0f} m"
        f"  {f_train['metres']:>8.0f} m"
        f"  {hw_train['minutes']:>10.1f} min"
        f"  {tv_train_co2e['minutes']:>9.1f} min"
        f"  {hh_train_co2e['minutes']:>9.1f} min"
    )
    print(
        f"  {'Per-meeting AI inference (usage-wtd mid)':<{w}}"
        f" {wt_combined['total_co2e_g']:>6.1f} g"
        f"  {c_meet['metres']:>6.0f} m"
        f"  {f_meet['metres']:>8.0f} m"
        f"  {hw_meet['seconds']:>10.0f} s"
        f"  {tv_meet_co2e['minutes']:>9.1f} min"
        f"  {hh_meet_co2e['seconds']:>9.1f} s"
    )
    print(
        f"  {'Monthly AWS hosting (April 2026)':<{w}}"
        f" {AWS_APR2026_CO2E_G:>5,} g"
        f"  {c_aws['km']:>6.1f} km"
        f"  {f_aws['pkm']:>8.1f} km"
        f"  {hw_aws['working_days']:>9.1f} days"
        f"  {tv_aws_co2e['hours']:>9.1f} h"
        f"  {hh_aws_co2e['hours']:>9.1f} h"
    )
    print()
    ratio = AWS_APR2026_CO2E_G / wt_combined["total_co2e_g"]
    print(f"  Hosting : per-meeting ratio  {AWS_APR2026_CO2E_G:,} ÷ {wt_combined['total_co2e_g']:.1f} = {ratio:,.0f}×")
    print()


def print_raw_figures() -> None:
    """Print all source constants and key derived values as a reference appendix."""
    asr = transcription_impact()
    st = simple_template()
    sec = section_template()
    dv = delivery_template()
    bm = basic_minutes()
    es = executive_summary()
    utd = user_template_document()
    llm_t = llm_training_impact()
    asr_t = asr_training_impact()
    wt = usage_weighted_impact()
    wt_combined = combined_impact(wt, asr)
    simple_combined = combined_impact(st, asr)

    _section("Appendix RAW — Part 1: Source Constants and Assumptions")
    print(f"  {'Constant':<52} {'Value':>16}  Notes / Reference")
    print(f"  {'-'*52} {'-'*16}  {'-'*34}")
    src_rows: list[tuple[str, str, str]] = [
        ("TRANSCRIPT_WORDS", f"{TRANSCRIPT_WORDS:,} words", "1-hour baseline"),
        ("NUM_SECTIONS", str(NUM_SECTIONS), "SectionTemplate default"),
        ("TOKENS_PER_WORD", str(TOKENS_PER_WORD), "Conservative estimate [B.1]"),
        (
            "ASR_CARBON_INTENSITY (GBR)",
            f"{ASR_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh",
            "EcoLogits ElectricityMixRepository [25]",
        ),
        (
            "TRAINING_CARBON_INTENSITY (USA)",
            f"{TRAINING_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh",
            "EcoLogits ElectricityMixRepository [25]",
        ),
        ("ASR_STUDY_TOTAL_ENERGY_KWH", f"{ASR_STUDY_TOTAL_ENERGY_KWH} kWh", "Whisper study [15]"),
        ("ASR_STUDY_AUDIO_HOURS", f"{ASR_STUDY_AUDIO_HOURS} h", "Study sample [15]"),
        ("ASR_STUDY_TOTAL_CO2E_G", f"{ASR_STUDY_TOTAL_CO2E_G} g", "Study measurement [15]"),
        (
            "GPT5_NANO_PARAMS_B (dense)",
            f"{GPT5_NANO_PARAMS_B.min}–{GPT5_NANO_PARAMS_B.max} B",
            "EcoLogits ModelRepository",
        ),
        ("GPT51_TOTAL_B (MoE total)", f"{GPT51_TOTAL_B} B", "EcoLogits ModelRepository"),
        ("GPT51_ACTIVE_B (MoE active)", f"{GPT51_ACTIVE_B.min}–{GPT51_ACTIVE_B.max} B", "EcoLogits ModelRepository"),
        ("OPENAI_PUE", str(OPENAI_PUE), "EcoLogits PROVIDER_CONFIG_MAP['openai']"),
        ("OPENAI_WUE", str(OPENAI_WUE), "EcoLogits PROVIDER_CONFIG_MAP['openai']"),
        ("UK_GWP_KG_PER_KWH (GBR)", f"{UK_GWP_KG_PER_KWH} kg/kWh", "EcoLogits ElectricityMixRepository"),
        (
            "LLM_CARBON_INTENSITY (GBR)",
            f"{LLM_CARBON_INTENSITY_G_PER_KWH:.2f} g/kWh",
            "EcoLogits ElectricityMixRepository [25]",
        ),
        ("GPT4_TRAINING_MWH (proxy)", f"{GPT4_TRAINING_MWH:,} MWh", "Proxy; GPT-5.x unpublished [11]"),
        ("GPT4O_TRAINING_MWH (proxy)", f"{GPT4O_TRAINING_MWH:,} MWh", "Proxy; GPT-5.x unpublished [11]"),
        ("LLM_USER_BASE", f"{LLM_USER_BASE:,}", "ChatGPT weekly active users [13]"),
        ("OWSM_GPU_COUNT", str(OWSM_GPU_COUNT), "NVIDIA A100 40GB PCIe [19][20]"),
        ("OWSM_GPU_TDP_W", f"{OWSM_GPU_TDP_W} W", "[20]"),
        ("OWSM_TRAINING_DAYS", f"{OWSM_TRAINING_DAYS} days", "[19]"),
        ("OWSM_PUE", str(OWSM_PUE), "Industry average 2024 [21]"),
        ("ASR_USER_BASE", f"{ASR_USER_BASE:,}", "MS Teams monthly active users [23]"),
        (
            "HOMEWORKING_OFFICE_EQUIPMENT",
            f"{HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR} kg/h",
            "UK GHG CF 2025 [HW]",
        ),
        ("HOMEWORKING_HEATING", f"{HOMEWORKING_HEATING_KG_CO2E_PER_HOUR} kg/h", "UK GHG CF 2025 [HW]"),
        ("HOMEWORKING_TOTAL", f"{HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg/h", "UK GHG CF 2025 [HW]"),
        ("CAR_AVG_PETROL_WLTP_GCO2_PER_KM", f"{CAR_AVG_PETROL_WLTP_GCO2_PER_KM} g/km", "UK GHG CF 2025 Table 15 [26]"),
        ("CAR_REAL_WORLD_UPLIFT_FRACTION", f"{CAR_REAL_WORLD_UPLIFT_FRACTION}", "UK GHG CF 2025 Table 16 [26]"),
        (
            "FLIGHT_LONG_HAUL_ECONOMY_BASE",
            f"{FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE} g/pkm",
            "UK GHG CF 2025 Table 39 [26]",
        ),
        ("FLIGHT_DISTANCE_UPLIFT_FRACTION", f"{FLIGHT_DISTANCE_UPLIFT_FRACTION}", "UK GHG CF 2025 §8.39 [26]"),
        ("FLIGHT_RF_MULTIPLIER", f"{FLIGHT_RF_MULTIPLIER}", "UK GHG CF 2025 §8.43 RF central [26]"),
        (
            "HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR",
            f"{HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR:,} kWh/yr",
            "Ofgem TDCV 2023 medium [27]",
        ),
        ("HOUSEHOLD_GAS_KWH_PER_YEAR", f"{HOUSEHOLD_GAS_KWH_PER_YEAR:,} kWh/yr", "Ofgem TDCV 2023 medium [27]"),
        ("TV_TYPICAL_WATTAGE", f"{TV_TYPICAL_WATTAGE} W", "indicative; EU/UK energy labels [28]"),
    ]
    for name, val, note in src_rows:
        print(f"  {name:<52} {val:>16}  {note}")

    _section("Appendix RAW — Part 2: Key Derived Values  [min–max range]")
    print(f"  {'Metric':<54} {'Value':>24}")
    print(f"  {'-'*54} {'-'*24}")
    der_rows: list[tuple[str, str]] = [
        ("ASR energy / hour of audio", f"{asr['energy_wh']:.4f} Wh"),
        ("ASR CO₂e / hour (study intensity)", f"{asr['co2e_g_study']:.4f} g"),
        ("ASR CO₂e / hour (GBR recalc)", f"{asr['co2e_g_eu27']:.4f} g"),
        (
            "SimpleTemplate   — out tok / Wh / g CO₂e",
            f"{st['total_out_tokens']:,.0f} tok  {_rng(st['total_wh_min'], st['total_wh_max'])} Wh  {_rng(st['gwp_g_min'], st['gwp_g_max'])} g",
        ),
        (
            "SectionTemplate  — out tok / Wh / g CO₂e",
            f"{sec['total_out_tokens']:,.0f} tok  {_rng(sec['total_wh_min'], sec['total_wh_max'])} Wh  {_rng(sec['gwp_g_min'], sec['gwp_g_max'])} g",
        ),
        (
            "DeliveryTemplate — out tok / Wh / g CO₂e",
            f"{dv['total_out_tokens']:,.0f} tok  {_rng(dv['total_wh_min'], dv['total_wh_max'])} Wh  {_rng(dv['gwp_g_min'], dv['gwp_g_max'])} g",
        ),
        (
            "BasicMinutes     — out tok / Wh / g CO₂e",
            f"{bm['total_out_tokens']:,.0f} tok  {_rng(bm['total_wh_min'], bm['total_wh_max'])} Wh  {_rng(bm['gwp_g_min'], bm['gwp_g_max'])} g",
        ),
        (
            "ExecutiveSummary — out tok / Wh / g CO₂e",
            f"{es['total_out_tokens']:,.0f} tok  {_rng(es['total_wh_min'], es['total_wh_max'])} Wh  {_rng(es['gwp_g_min'], es['gwp_g_max'])} g",
        ),
        (
            "UserTemplate Doc — out tok / Wh / g CO₂e",
            f"{utd['total_out_tokens']:,.0f} tok  {_rng(utd['total_wh_min'], utd['total_wh_max'])} Wh  {_rng(utd['gwp_g_min'], utd['gwp_g_max'])} g",
        ),
        (
            "SimpleTemplate combined (+ ASR GBR)",
            _rng(simple_combined["total_co2e_g_min"], simple_combined["total_co2e_g_max"], "g CO₂e"),
        ),
        (
            "Usage-weighted LLM + ASR CO₂e",
            _rng(wt_combined["total_co2e_g_min"], wt_combined["total_co2e_g_max"], "g CO₂e"),
        ),
        (
            "Usage-weighted total energy",
            _rng(wt_combined["total_energy_wh_min"], wt_combined["total_energy_wh_max"], "Wh"),
        ),
        ("GPT-4 training — per user energy (proxy)", f"{llm_t['gpt4_per_user_wh']:.4f} Wh"),
        ("GPT-4o training — per user energy (proxy)", f"{llm_t['gpt4o_per_user_wh']:.6f} Wh"),
        ("LLM combined training — per user CO₂e (proxy)", f"{llm_t['llm_total_co2e']:.4f} g"),
        ("ASR (OWSM) training — per user energy", f"{asr_t['per_user_wh']:.6f} Wh"),
        ("ASR (OWSM) training — per user CO₂e", f"{asr_t['co2e_g']:.6f} g"),
        ("Homeworking rate (combined)", f"{HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR * 1000:.3f} g CO₂e/h"),
        (
            "Usage-weighted meeting ≡ homeworking (mid)",
            f"{homeworking_displacement(wt_combined['total_co2e_g'])['seconds']:.2f} s",
        ),
        (
            "SimpleTemplate meeting ≡ homeworking (mid)",
            f"{homeworking_displacement(simple_combined['total_co2e_g'])['seconds']:.2f} s",
        ),
        (
            "Car real-world emission factor (avg petrol, Scope 1)",
            f"{car_displacement(1.0)['g_per_km']:.2f} g CO₂/km",
        ),
        (
            "Flight factor (long-haul economy, incl. RF×1.7)",
            f"{flight_displacement(1.0)['g_per_pkm']:.2f} g CO₂e/pkm",
        ),
        (
            "Household daily energy (2023 TDCVs, medium)",
            f"{household_energy_fraction(1.0)['daily_wh']:,.0f} Wh",
        ),
        (
            "Usage-weighted → petrol car distance (mid)",
            f"{car_displacement(wt_combined['total_co2e_g'])['metres']:.1f} m",
        ),
        (
            "Usage-weighted → long-haul flight distance (mid)",
            f"{flight_displacement(wt_combined['total_co2e_g'])['metres']:.1f} m",
        ),
        (
            "Usage-weighted → TV viewing time (mid)",
            f"{tv_displacement(wt_combined['total_energy_wh'])['minutes']:.1f} min",
        ),
        (
            "Usage-weighted → household energy fraction (mid)",
            f"{household_energy_fraction(wt_combined['total_energy_wh'])['percent']:.4f} %",
        ),
    ]
    for metric, val in der_rows:
        print(f"  {metric:<54} {val:>24}")
    print()


# =============================================================================
# AWS SUSTAINABILITY API — live monthly carbon report
# =============================================================================

_MTCO2E_TO_G = 1_000_000  # 1 MTCO2e = 1,000,000 g CO₂e
_MTCO2E_TO_KG = 1_000  # 1 MTCO2e = 1,000 kg CO₂e


def last_month_window() -> tuple[str, str, str]:
    """Return (start_iso, end_iso, human_label) for the previous calendar month."""
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)
    label = last_month_start.strftime("%B %Y")
    return (
        last_month_start.strftime("%Y-%m-%dT00:00:00Z"),
        first_of_this_month.strftime("%Y-%m-%dT00:00:00Z"),
        label,
    )


def fetch_aws_emissions(start: str, end: str) -> dict:
    """Call `aws sustainability get-estimated-carbon-emissions` and return the first result."""
    time_period = json.dumps({"Start": start, "End": end})
    try:
        proc = subprocess.run(
            [
                "aws",
                "sustainability",
                "get-estimated-carbon-emissions",
                "--time-period",
                time_period,
                "--region",
                "us-east-1",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        msg = f"AWS CLI returned a non-zero exit code:\n{exc.stderr.strip()}"
        raise RuntimeError(msg) from exc
    except FileNotFoundError as exc:
        msg = "AWS CLI not found — install it and configure credentials first."
        raise RuntimeError(msg) from exc

    data = json.loads(proc.stdout)
    results = data.get("Results", [])
    if not results:
        msg = "AWS Sustainability API returned no results for the requested period."
        raise RuntimeError(msg)
    return results[0]


def print_aws_report() -> None:
    """Fetch last month's AWS emissions and contextualise against per-meeting AI cost."""
    start, end, label = last_month_window()

    print(f"\nAWS INFRASTRUCTURE CARBON EMISSIONS — {label}")
    print(f"  Querying {start[:10]} → {end[:10]} (exclusive end) …")

    aws = fetch_aws_emissions(start, end)
    emissions = aws["EmissionsValues"]
    model_version = aws.get("ModelVersion", "unknown")

    lbm_mtco2e: float = emissions["TOTAL_LBM_CARBON_EMISSIONS"]["Value"]
    mbm_mtco2e: float = emissions["TOTAL_MBM_CARBON_EMISSIONS"]["Value"]
    lbm_g = lbm_mtco2e * _MTCO2E_TO_G
    mbm_g = mbm_mtco2e * _MTCO2E_TO_G
    lbm_kg = lbm_mtco2e * _MTCO2E_TO_KG
    mbm_kg = mbm_mtco2e * _MTCO2E_TO_KG

    _section(f"AWS Sustainability API — {label}  [model {model_version}]")
    _row("Period", f"{start[:10]} – {end[:10]}")
    _row(
        "Market-based    (MBM) ★ primary",
        f"{mbm_mtco2e:.6f} MTCO2e  =  {mbm_kg:.3f} kg  =  {mbm_g:,.0f} g CO₂e",
    )
    _row(
        "Location-based  (LBM) reference",
        f"{lbm_mtco2e:.6f} MTCO2e  =  {lbm_kg:.3f} kg  =  {lbm_g:,.0f} g CO₂e",
    )
    print()
    print("  MBM  subtracts renewable-energy certificates (RECs) purchased by AWS;")
    print("       used for comparisons because AWS actively buys clean energy.")
    print("  LBM  uses regional grid averages (shown for reference).")

    asr = transcription_impact()
    wt = usage_weighted_impact(TRANSCRIPT_WORDS, NUM_SECTIONS)
    wt_combined = combined_impact(wt, asr)
    per_hour_g = wt_combined["total_co2e_g"]

    _section("AI Processing Cost — per 1-hour meeting  [from calculations.py]")
    _row("Usage-weighted CO₂e / hour", f"{per_hour_g:.1f} g CO₂e")
    _row("Scope", "Transcription (ASR) + LLM inference, EU-27 grid intensity")

    if per_hour_g > 0:
        mbm_eq = mbm_g / per_hour_g
        lbm_eq = lbm_g / per_hour_g

        _section(f"Context — {label} AWS infra vs. AI processing cost per hour")
        _row(
            "MBM ÷ AI cost per hour",
            f"{mbm_g:,.0f} g ÷ {per_hour_g:.1f} g  ≈  {mbm_eq:,.0f} hours of AI processing",
        )
        _row(
            "LBM ÷ AI cost per hour (ref)",
            f"{lbm_g:,.0f} g ÷ {per_hour_g:.1f} g  ≈  {lbm_eq:,.0f} hours of AI processing",
        )
        print()
        print(f"  → The AWS hosting layer for {label} emitted ~{mbm_eq:,.0f}× the AI cost")
        print("    of a single 1-hour meeting (MBM, market-adjusted basis).")
        print()
        print("  ⚠  AWS figure = all account services (EC2, RDS, S3, networking, …).")
        print("  AI figure = transcription + LLM inference on Azure/OpenAI — different layer.")
        print("  Together they represent the two distinct slices of total system footprint.")

    hw_meeting = homeworking_displacement(per_hour_g)
    hw_hosting_mbm = homeworking_displacement(mbm_g)

    _section(f"Homeworking Displacement  [UK GHG CF 2025] — {label}")
    print("  Source: UK Government GHG Conversion Factors 2025 (DESNZ/DEFRA)")
    print("  https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025")
    print(f"  Rate: {HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    print("        (office equipment 0.03144 + heating 0.30234, Scope 1+2)")
    print()
    print("  ─── One 1-hour meeting — AI processing only ───────────────────────")
    _row("Meeting AI CO₂e (usage-weighted)", f"{per_hour_g:.2f} g CO₂e")
    _row(
        "≡ homeworking",
        f"{hw_meeting['seconds']:.1f} s  ({hw_meeting['minutes']:.3f} min  /  {hw_meeting['hours']:.5f} h)",
    )
    print()
    print("  ─── One month of AWS hosting (MBM, market-adjusted) ───────────────")
    _row("Monthly hosting CO₂e (MBM)", f"{mbm_g:,.0f} g  ({mbm_kg:.3f} kg)")
    _row(
        "≡ homeworking",
        f"{hw_hosting_mbm['hours']:,.1f} h  "
        f"({hw_hosting_mbm['working_days']:,.1f} working day(s) at {WORKING_HOURS_PER_DAY} h/day)",
    )
    print()
    if hw_meeting["hours"] > 0:
        hw_ratio = hw_hosting_mbm["hours"] / hw_meeting["hours"]
        print(f"  → Monthly AWS hosting ≡ {hw_hosting_mbm['working_days']:,.1f} working-day(s) of homeworking.")
        print(f"    AI processing per meeting ≡ {hw_meeting['seconds']:.0f} seconds of homeworking.")
        print(f"    The hosting layer is ~{hw_ratio:,.0f}× more carbon-intensive (per month vs. per meeting).")
        print()
        print("  Conclusion: reducing AWS infrastructure (right-sizing, switching off idle")
        print("  resources) delivers far greater carbon savings than optimising AI prompt")
        print("  length. The per-meeting AI cost is negligible against the hosting baseline.")
    print()


if __name__ == "__main__":
    print_results()
    print_raw_figures()
    try:
        print_aws_report()
    except RuntimeError as e:
        print(f"\n[AWS report skipped: {e}]")
