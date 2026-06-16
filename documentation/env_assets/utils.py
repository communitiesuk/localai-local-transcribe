"""Shared constants, EcoLogits setup, and display utilities.

All assumption values are loaded from assumptions.yaml.
EcoLogits-derived values (model params, grid intensity, datacenter config)
are fetched once at import time.
"""

from pathlib import Path

import yaml
from ecologits.electricity_mix_repository import ElectricityMixRepository
from ecologits.impacts.llm import compute_llm_impacts  # re-exported for llm_inference
from ecologits.model_repository import ModelRepository
from ecologits.tracers.utils import PROVIDER_CONFIG_MAP
from ecologits.utils.range_value import RangeValue

_cfg = yaml.safe_load((Path(__file__).parent / "assumptions.yaml").read_text())

# =============================================================================
# EcoLogits — fetched once at import
# =============================================================================

_openai_cfg = PROVIDER_CONFIG_MAP["openai"]
_elec_repo = ElectricityMixRepository.from_json()
_uk_mix = _elec_repo.find_electricity_mix(zone="GBR")
_usa_mix = _elec_repo.find_electricity_mix(zone="USA")
_model_repo = ModelRepository.from_json()
_nano_model = _model_repo.find_model(provider="openai", model_name="gpt-5-nano")
_best_model = _model_repo.find_model(provider="openai", model_name="gpt-5.1")

# =============================================================================
# Constants from assumptions.yaml
# =============================================================================

TRANSCRIPT_WORDS: int = _cfg["meeting"]["transcript_words"]
NUM_SECTIONS: int = _cfg["meeting"]["num_sections"]
TOKENS_PER_WORD: int = _cfg["meeting"]["tokens_per_word"]

ASR_STUDY_TOTAL_ENERGY_KWH: float = _cfg["asr_study"]["total_energy_kwh"]
ASR_STUDY_AUDIO_HOURS: int = _cfg["asr_study"]["audio_hours"]
ASR_STUDY_TOTAL_CO2E_G: int = _cfg["asr_study"]["total_co2e_g"]

GPT4_TRAINING_MWH: int = _cfg["llm_training"]["gpt4_mwh"]
GPT4O_TRAINING_MWH: int = _cfg["llm_training"]["gpt4o_mwh"]
LLM_USER_BASE: int = _cfg["llm_training"]["user_base"]

OWSM_GPU_COUNT: int = _cfg["owsm_training"]["gpu_count"]
OWSM_GPU_TDP_W: int = _cfg["owsm_training"]["gpu_tdp_w"]
OWSM_TRAINING_DAYS: int = _cfg["owsm_training"]["training_days"]
OWSM_SERVER_GPU_DRAW_W: int = _cfg["owsm_training"]["server_gpu_draw_w"]
OWSM_SERVER_NON_GPU_LOW_W: int = _cfg["owsm_training"]["server_non_gpu_low_w"]
OWSM_SERVER_NON_GPU_HIGH_W: int = _cfg["owsm_training"]["server_non_gpu_high_w"]
OWSM_PUE: float = _cfg["owsm_training"]["pue"]
ASR_USER_BASE: int = _cfg["owsm_training"]["user_base"]

HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR: float = _cfg["homeworking"]["office_equipment_kg_co2e_per_hour"]
HOMEWORKING_HEATING_KG_CO2E_PER_HOUR: float = _cfg["homeworking"]["heating_kg_co2e_per_hour"]
HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR: float = _cfg["homeworking"]["total_kg_co2e_per_hour"]
WORKING_HOURS_PER_DAY: int = _cfg["homeworking"]["working_hours_per_day"]

AWS_APR2026_CO2E_G: int = _cfg["aws"]["apr2026_co2e_g"]

CAR_AVG_PETROL_WLTP_GCO2_PER_KM: float = _cfg["car"]["avg_petrol_wltp_gco2_per_km"]
CAR_REAL_WORLD_UPLIFT_FRACTION: float = _cfg["car"]["real_world_uplift_fraction"]

FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE: float = _cfg["flight"]["long_haul_economy_gco2_per_pkm_base"]
FLIGHT_DISTANCE_UPLIFT_FRACTION: float = _cfg["flight"]["distance_uplift_fraction"]
FLIGHT_RF_MULTIPLIER: float = _cfg["flight"]["rf_multiplier"]

TV_TYPICAL_WATTAGE: int = _cfg["television"]["typical_wattage"]

HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR: int = _cfg["household"]["electricity_kwh_per_year"]
HOUSEHOLD_GAS_KWH_PER_YEAR: int = _cfg["household"]["gas_kwh_per_year"]

# =============================================================================
# Derived constants — computed from EcoLogits API
# =============================================================================

ASR_CARBON_INTENSITY_G_PER_KWH: float = _uk_mix.gwp * 1000
TRAINING_CARBON_INTENSITY_G_PER_KWH: float = _usa_mix.gwp * 1000
LLM_CARBON_INTENSITY_G_PER_KWH: float = _uk_mix.gwp * 1000

GPT5_NANO_PARAMS_B: RangeValue = _nano_model.architecture.parameters
GPT5_NANO_TPS: float = _nano_model.deployment.tps
GPT5_NANO_TTFT: float = _nano_model.deployment.ttft

GPT51_TOTAL_B: int = _best_model.architecture.parameters.total
GPT51_ACTIVE_B: RangeValue = _best_model.architecture.parameters.active
GPT51_TPS: float = _best_model.deployment.tps
GPT51_TTFT: float = _best_model.deployment.ttft

OPENAI_PUE: float = _openai_cfg.datacenter_pue
OPENAI_WUE: float = _openai_cfg.datacenter_wue

UK_GWP_KG_PER_KWH: float = _uk_mix.gwp
UK_ADPE: float = _uk_mix.adpe
UK_PE: float = _uk_mix.pe
UK_WUE: float = _uk_mix.wue

# =============================================================================
# Shared utilities
# =============================================================================


def words_to_tokens(words: float) -> float:
    return words * TOKENS_PER_WORD


def combined_impact(llm: dict, asr: dict) -> dict:
    """Merge LLM and ASR results into a single combined-impact dict."""
    energy_min = llm["total_wh_min"] + asr["energy_wh"]
    energy_max = llm["total_wh_max"] + asr["energy_wh"]
    co2e_min = llm["gwp_g_min"] + asr["co2e_g_eu27"]
    co2e_max = llm["gwp_g_max"] + asr["co2e_g_eu27"]
    co2e_mid = (co2e_min + co2e_max) / 2
    return {
        "total_energy_wh_min": energy_min,
        "total_energy_wh_max": energy_max,
        "total_energy_wh": (energy_min + energy_max) / 2,
        "total_co2e_g_min": co2e_min,
        "total_co2e_g_max": co2e_max,
        "total_co2e_g": co2e_mid,
        "asr_pct": 100 * asr["co2e_g_eu27"] / co2e_mid if co2e_mid else 0,
        "llm_pct": 100 * llm["co2e_g"] / co2e_mid if co2e_mid else 0,
    }


def _section(title: str) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print("=" * 62)


def _row(label: str, value: str) -> None:
    print(f"  {label:<44} {value}")


def _rng(lo: float, hi: float, unit: str = "", dp: int = 1) -> str:
    fmt = f".{dp}f"
    return f"{lo:{fmt}}–{hi:{fmt}} {unit}".strip()
