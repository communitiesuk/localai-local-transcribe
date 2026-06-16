"""Section 6: Transcription (ASR) impact for a 1-hour meeting."""

from utils import (
    ASR_CARBON_INTENSITY_G_PER_KWH,
    ASR_STUDY_AUDIO_HOURS,
    ASR_STUDY_TOTAL_CO2E_G,
    ASR_STUDY_TOTAL_ENERGY_KWH,
    _row,
    _section,
)


def calculate() -> dict:
    energy_wh = (ASR_STUDY_TOTAL_ENERGY_KWH * 1_000) / ASR_STUDY_AUDIO_HOURS
    return {
        "energy_wh": energy_wh,
        "co2e_g_study": ASR_STUDY_TOTAL_CO2E_G / ASR_STUDY_AUDIO_HOURS,
        "co2e_g_eu27": (energy_wh / 1_000) * ASR_CARBON_INTENSITY_G_PER_KWH,
    }


def display() -> None:
    r = calculate()
    _section("Section 6: Transcription (1-hour meeting)")
    _row("Source: total energy over study", f"{ASR_STUDY_TOTAL_ENERGY_KWH} kWh / {ASR_STUDY_AUDIO_HOURS} hours")
    _row(
        "Energy per hour",
        f"{ASR_STUDY_TOTAL_ENERGY_KWH * 1000} Wh / {ASR_STUDY_AUDIO_HOURS} h"
        f"  = {r['energy_wh']:.2f} Wh  ({r['energy_wh'] / 1000:.4f} kWh)",
    )
    _row(
        "CO₂e (study carbon intensity)",
        f"{ASR_STUDY_TOTAL_CO2E_G} g / {ASR_STUDY_AUDIO_HOURS} h  = {r['co2e_g_study']:.2f} g",
    )
    _row(
        "CO₂e (GBR, used in combined totals)",
        f"{r['energy_wh']:.2f} Wh × {ASR_CARBON_INTENSITY_G_PER_KWH:.1f} g/kWh / 1000"
        f"  = {r['co2e_g_eu27']:.2f} g",
    )


if __name__ == "__main__":
    display()
