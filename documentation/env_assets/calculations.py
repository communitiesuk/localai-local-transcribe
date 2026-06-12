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

from ecologits.electricity_mix_repository import ElectricityMixRepository
from ecologits.impacts.llm import compute_llm_impacts
from ecologits.model_repository import ModelRepository
from ecologits.tracers.utils import PROVIDER_CONFIG_MAP
from ecologits.utils.range_value import RangeValue

# Load all grid/datacenter/model data from EcoLogits at import time.
_openai_cfg = PROVIDER_CONFIG_MAP["openai"]
_elec_repo = ElectricityMixRepository.from_json()
_uk_mix = _elec_repo.find_electricity_mix(zone="GBR")
_usa_mix = _elec_repo.find_electricity_mix(zone="USA")
_model_repo = ModelRepository.from_json()
_nano_model = _model_repo.find_model(provider="openai", model_name="gpt-5-nano")
_best_model = _model_repo.find_model(provider="openai", model_name="gpt-5.1")

# =============================================================================
# ASSUMPTIONS — source/measured values; edit these to model different scenarios
# =============================================================================

# --- Meeting / transcript ---
TRANSCRIPT_WORDS = 9_000  # X: words in transcript (1-hour baseline, ~7,500–9,000 typical)
NUM_SECTIONS = 6  # Y: sections produced by SectionTemplate
TOKENS_PER_WORD = 2  # conservative estimate for English text [B.1]

# --- Carbon intensity (all loaded from EcoLogits ElectricityMixRepository) ---
# ASR transcription runs on our own infrastructure in the UK.
ASR_CARBON_INTENSITY_G_PER_KWH: float = _uk_mix.gwp * 1000  # GBR, ≈217 g/kWh [25]
# LLM training happened in US data centres.
TRAINING_CARBON_INTENSITY_G_PER_KWH: float = _usa_mix.gwp * 1000  # USA, ≈384 g/kWh [25]

# --- ASR (transcription) — measurements from study [15], Whisper proxy ---
ASR_STUDY_TOTAL_ENERGY_KWH = 0.49  # kWh measured over the study sample
ASR_STUDY_AUDIO_HOURS = 22  # hours of audio in the study sample
ASR_STUDY_TOTAL_CO2E_G = 380  # g CO₂e measured over the study sample
# Note: the study's implied carbon intensity (~776 g/kWh) differs from GBR.
# CO₂e for combined totals (Section 8) is recalculated using GBR for consistency.

# --- LLM models (loaded from EcoLogits ModelRepository at import time) ---
# GPT-5-nano  — dense architecture; active == total
GPT5_NANO_PARAMS_B: RangeValue = _nano_model.architecture.parameters
GPT5_NANO_TPS: float = _nano_model.deployment.tps
GPT5_NANO_TTFT: float = _nano_model.deployment.ttft

# GPT-5.1     — MoE architecture
GPT51_TOTAL_B: int = _best_model.architecture.parameters.total
GPT51_ACTIVE_B: RangeValue = _best_model.architecture.parameters.active
GPT51_TPS: float = _best_model.deployment.tps
GPT51_TTFT: float = _best_model.deployment.ttft

# --- OpenAI data-centre configuration (from EcoLogits PROVIDER_CONFIG_MAP['openai']) ---
OPENAI_PUE: float = _openai_cfg.datacenter_pue  # Power Usage Effectiveness
OPENAI_WUE: float = _openai_cfg.datacenter_wue  # Water Usage Effectiveness (L/kWh)

# --- UK electricity mix (from EcoLogits ElectricityMixRepository, zone='GBR') ---
# Used for the energy calculation in EcoLogits (affects embodied hardware estimates).
UK_GWP_KG_PER_KWH: float = _uk_mix.gwp  # ≈ 217 g CO₂eq/kWh  [gwp]
UK_ADPE: float = _uk_mix.adpe  # kg Sb-eq / kWh      [adpe]
UK_PE: float = _uk_mix.pe  # MJ / kWh            [pe]
UK_WUE: float = _uk_mix.wue  # L / kWh             [wue]

# --- LLM inference carbon intensity (old derivation method) ---
# CO₂e for LLM inference is computed as: energy_kWh × LLM_CARBON_INTENSITY_G_PER_KWH.
# GBR (UK) grid intensity from EcoLogits ElectricityMixRepository.
LLM_CARBON_INTENSITY_G_PER_KWH: float = _uk_mix.gwp * 1000  # ≈ 217 g/kWh GBR

# --- LLM training energy [11] ---
# GPT-5.x training costs are not publicly available.
# GPT-4 / GPT-4o figures used as order-of-magnitude proxies (likely underestimates).
GPT4_TRAINING_MWH = 57_000  # midpoint of 52k–62k MWh range
GPT4O_TRAINING_MWH = 1_151  # Gopher (280B params) proxy for GPT-4o (~200B params)

# --- LLM user base [13] ---
LLM_USER_BASE = 800_000_000  # ChatGPT weekly active users at peak

# --- Executive Summary (executive_summary.j2) ---
EXEC_SUMMARY_SYSTEM_WORDS = 129  # counted directly from executive_summary.j2

# --- UserTemplate DOCUMENT (user_template.py document_prompt) ---
DOCUMENT_PROMPT_FIXED_WORDS = 115  # fixed words in document_prompt, excluding {template} and {date}
USER_TEMPLATE_CONTENT_WORDS = 200  # user-defined template content (assumption; varies in practice)
DOCUMENT_DATE_WORDS = 7  # formatted datetime, e.g. "Monday 22 May 2026 14:30:00"

# --- OWSM v3 training hardware [19][20][21][22] ---
OWSM_GPU_COUNT = 64  # NVIDIA A100 40GB PCIe GPUs used
OWSM_GPU_TDP_W = 250  # TDP per GPU in watts [20]
OWSM_TRAINING_DAYS = 10  # duration of training run
OWSM_SERVER_GPU_DRAW_W = 3_200  # GPU power draw for a server with 8 A100s [22]
OWSM_SERVER_NON_GPU_LOW_W = 500  # lower bound, non-GPU components [22]
OWSM_SERVER_NON_GPU_HIGH_W = 1_000  # upper bound, non-GPU components [22]
OWSM_PUE = 1.56  # industry average PUE 2024 [21]

# --- ASR user base [23] ---
ASR_USER_BASE = 300_000_000  # Microsoft Teams monthly active users

# --- Homeworking emission factors [HW] ---
# Source: UK Government GHG Conversion Factors 2025 (DESNZ/DEFRA)
# https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025
# Table: "Homeworking" — per FTE working hour, Scope 1+2 combined
HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR = 0.03144
HOMEWORKING_HEATING_KG_CO2E_PER_HOUR = 0.30234
HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR = 0.33378  # office equipment + heating

WORKING_HOURS_PER_DAY = 8  # standard working day used for homeworking comparisons


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

# (template_name, production_share, implementation)
# Shares sum to 1.0.
TEMPLATE_USAGE_SHARES: list[tuple[str, float, str]] = [
    ("General", 0.5241, "SimpleTemplate"),  # General 51.32% + general 1.09%
    ("Delivery", 0.1523, "DeliveryTemplate"),  # Delivery 14.83% + delivery 0.40%
    ("Short 'n' Sweet", 0.1234, "ExecutiveSummary (SimpleTemplate, no citations)"),
    ("User generated", 0.0960, "UserTemplate DOCUMENT"),
    ("Cabinet", 0.0589, "SectionTemplate (Y=6)"),  # Cabinet 5.58% + cabinet 0.31%
    ("Care Assessment", 0.0261, "SimpleTemplate (deprecated v1, assumed)"),
    ("Planning Committee", 0.0120, "SectionTemplate (Y=6)"),
    ("Care Assessment V2", 0.0073, "SimpleTemplate"),
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
    ]
    for metric, val in der_rows:
        print(f"  {metric:<54} {val:>24}")
    print()


if __name__ == "__main__":
    print_results()
    print_raw_figures()
