"""Section 8 + Appendix G: combined per-meeting impact and real-world activity comparisons."""

from utils import (
    AWS_APR2026_CO2E_G,
    CAR_AVG_PETROL_WLTP_GCO2_PER_KM,
    CAR_REAL_WORLD_UPLIFT_FRACTION,
    FLIGHT_DISTANCE_UPLIFT_FRACTION,
    FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE,
    FLIGHT_RF_MULTIPLIER,
    HOMEWORKING_HEATING_KG_CO2E_PER_HOUR,
    HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR,
    HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR,
    HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR,
    HOUSEHOLD_GAS_KWH_PER_YEAR,
    LLM_CARBON_INTENSITY_G_PER_KWH,
    TV_TYPICAL_WATTAGE,
    WORKING_HOURS_PER_DAY,
    combined_impact,
    _rng,
    _row,
    _section,
)

# =============================================================================
# Displacement helpers
# =============================================================================


def homeworking_displacement(co2e_g: float) -> dict:
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
    g_per_km = CAR_AVG_PETROL_WLTP_GCO2_PER_KM * (1 + CAR_REAL_WORLD_UPLIFT_FRACTION)
    km = co2e_g / g_per_km
    return {"g_per_km": g_per_km, "km": km, "metres": km * 1_000}


def flight_displacement(co2e_g: float) -> dict:
    g_per_pkm = (
        FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE * (1 + FLIGHT_DISTANCE_UPLIFT_FRACTION) * FLIGHT_RF_MULTIPLIER
    )
    pkm = co2e_g / g_per_pkm
    return {"g_per_pkm": g_per_pkm, "pkm": pkm, "metres": pkm * 1_000}


def tv_displacement(energy_wh: float) -> dict:
    minutes = energy_wh * 60 / TV_TYPICAL_WATTAGE
    return {"wattage": TV_TYPICAL_WATTAGE, "minutes": minutes}


def tv_co2e_time(co2e_g: float) -> dict:
    g_per_min = TV_TYPICAL_WATTAGE * LLM_CARBON_INTENSITY_G_PER_KWH / 1_000 / 60
    return {"g_per_min": g_per_min, "minutes": co2e_g / g_per_min, "hours": co2e_g / g_per_min / 60}


def household_co2e_time(co2e_g: float) -> dict:
    daily_wh = (HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR + HOUSEHOLD_GAS_KWH_PER_YEAR) / 365 * 1_000
    avg_w = daily_wh / 24
    g_per_s = avg_w * LLM_CARBON_INTENSITY_G_PER_KWH / 1_000 / 3_600
    seconds = co2e_g / g_per_s
    return {"avg_w": avg_w, "g_per_s": g_per_s, "seconds": seconds, "minutes": seconds / 60, "hours": seconds / 3_600}


def household_energy_fraction(energy_wh: float) -> dict:
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
# Public interface
# =============================================================================


def calculate() -> dict:
    import llm_inference
    import transcription
    import training

    asr = transcription.calculate()
    llm = llm_inference.calculate()
    training_r = training.calculate()

    wt_combined = combined_impact(llm["usage_weighted"], asr)
    simple_combined = combined_impact(llm["simple_template"], asr)
    template_combined = {name: combined_impact(result, asr) for name, result in llm["by_template"].items()}

    training_co2e = training_r["llm"]["llm_total_co2e"] + training_r["asr"]["co2e_g"]
    training_wh = training_r["llm"]["llm_total_wh"] + training_r["asr"]["per_user_wh"]

    return {
        "asr": asr,
        "llm": llm,
        "training_r": training_r,
        "wt_combined": wt_combined,
        "simple_combined": simple_combined,
        "template_combined": template_combined,
        "training_co2e": training_co2e,
        "training_wh": training_wh,
    }


def display() -> None:
    from llm_inference import TEMPLATE_USAGE_SHARES, NUM_SECTIONS

    r = calculate()
    asr = r["asr"]
    llm = r["llm"]
    wt_combined = r["wt_combined"]
    simple_combined = r["simple_combined"]
    training_co2e = r["training_co2e"]
    training_wh = r["training_wh"]

    # Section 8: combined impact per template
    _section("Section 8: Combined Impact per 1-Hour Meeting")
    print("  (ASR CO₂e at GBR 217 g/kWh; LLM CO₂e at GBR 217 g/kWh; energy via EcoLogits [25])\n")
    print(f"  {'Template':<30} {'Energy (Wh)':>20} {'CO₂e (g)':>20} {'ASR%':>6} {'LLM%':>6}")
    print(f"  {'-'*30} {'-'*20} {'-'*20} {'-'*6} {'-'*6}")
    for name, inv, tr in [
        ("Basic Minutes", "4", llm["basic_minutes"]),
        ("Short 'n' Sweet (no citations)", "4", llm["executive_summary"]),
        ("UserTemplate DOCUMENT", "4", llm["user_template_document"]),
        ("Delivery", "6", llm["delivery_template"]),
        ("SimpleTemplate", "6", llm["simple_template"]),
        (f"SectionTemplate Y={NUM_SECTIONS}", f"5+2×{NUM_SECTIONS}={5 + 2 * NUM_SECTIONS}", llm["section_template"]),
    ]:
        c = combined_impact(tr, asr)
        print(
            f"  {name:<30} {_rng(c['total_energy_wh_min'], c['total_energy_wh_max']):>20}"
            f" {_rng(c['total_co2e_g_min'], c['total_co2e_g_max']):>20}"
            f" {c['asr_pct']:>5.1f}% {c['llm_pct']:>5.1f}%"
        )

    # Appendix HW: homeworking displacement
    hw_wt_min = homeworking_displacement(wt_combined["total_co2e_g_min"])
    hw_wt_max = homeworking_displacement(wt_combined["total_co2e_g_max"])
    hw_st_min = homeworking_displacement(simple_combined["total_co2e_g_min"])
    hw_st_max = homeworking_displacement(simple_combined["total_co2e_g_max"])
    heating_pct = HOMEWORKING_HEATING_KG_CO2E_PER_HOUR / HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR * 100

    _section("Appendix HW: Homeworking Displacement  [UK GHG CF 2025]")
    print("  Source: UK Government GHG Conversion Factors 2025 (DESNZ/DEFRA)")
    print("  https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025")
    print("  Category: Homeworking (office equipment + heating), per FTE working hour, Scope 1+2.")
    print()
    _row("Office equipment", f"{HOMEWORKING_OFFICE_EQUIPMENT_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    _row("Heating", f"{HOMEWORKING_HEATING_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    _row("Combined (homeworking total)", f"{HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    print()
    _row(
        "Usage-weighted meeting CO₂e", _rng(wt_combined["total_co2e_g_min"], wt_combined["total_co2e_g_max"], "g CO₂e")
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
    print(f"  → Processing one 1-hour meeting emits the same CO₂e as ~{wt_sec_mid:.0f} seconds of homeworking")
    print(f"    (usage-weighted midpoint, rate = {HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e/h).")
    print(f"  → Heating accounts for {heating_pct:.0f}% of the homeworking factor.")
    print()

    # Appendix HW.2: additional activity comparisons
    car_wt_min = car_displacement(wt_combined["total_co2e_g_min"])
    car_wt_max = car_displacement(wt_combined["total_co2e_g_max"])
    flight_wt_min = flight_displacement(wt_combined["total_co2e_g_min"])
    flight_wt_max = flight_displacement(wt_combined["total_co2e_g_max"])
    tv_wt_min = tv_displacement(wt_combined["total_energy_wh_min"])
    tv_wt_max = tv_displacement(wt_combined["total_energy_wh_max"])
    hh_wt_min = household_energy_fraction(wt_combined["total_energy_wh_min"])
    hh_wt_max = household_energy_fraction(wt_combined["total_energy_wh_max"])
    car_g_per_km = CAR_AVG_PETROL_WLTP_GCO2_PER_KM * (1 + CAR_REAL_WORLD_UPLIFT_FRACTION)
    flight_g_per_pkm = (
        FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE * (1 + FLIGHT_DISTANCE_UPLIFT_FRACTION) * FLIGHT_RF_MULTIPLIER
    )
    hh_daily_wh = (HOUSEHOLD_ELECTRICITY_KWH_PER_YEAR + HOUSEHOLD_GAS_KWH_PER_YEAR) / 365 * 1_000

    _section("Appendix HW.2: Activity Comparisons [26][27][28]")
    print("  Car and flight use a CO₂e basis; TV and household use an energy basis.")
    print()
    _row(
        "Car real-world factor (avg petrol, Scope 1)",
        f"{CAR_AVG_PETROL_WLTP_GCO2_PER_KM} × (1+{CAR_REAL_WORLD_UPLIFT_FRACTION})  = {car_g_per_km:.1f} g CO₂/km  [26]",
    )
    _row(
        "Usage-weighted CO₂e → petrol car",
        f"{_rng(wt_combined['total_co2e_g_min'], wt_combined['total_co2e_g_max'], 'g')}  →  {_rng(car_wt_min['metres'], car_wt_max['metres'], 'm')}",
    )
    print()
    _row(
        "Flight factor (long-haul economy, incl. RF)",
        f"{FLIGHT_LONG_HAUL_ECONOMY_GCO2_PER_PKM_BASE} × 1.08 × {FLIGHT_RF_MULTIPLIER}  = {flight_g_per_pkm:.1f} g CO₂e/pkm  [26]",
    )
    _row(
        "Usage-weighted CO₂e → long-haul flight",
        f"{_rng(wt_combined['total_co2e_g_min'], wt_combined['total_co2e_g_max'], 'g')}  →  {_rng(flight_wt_min['metres'], flight_wt_max['metres'], 'm')}",
    )
    print()
    _row("Household daily energy (2,700+11,500 kWh/yr ÷ 365)", f"{hh_daily_wh:,.0f} Wh/day  [27]")
    _row(
        "Usage-weighted energy → household time",
        f"{_rng(wt_combined['total_energy_wh_min'], wt_combined['total_energy_wh_max'], 'Wh')}  →  {_rng(hh_wt_min['seconds'], hh_wt_max['seconds'], 's')}  ({_rng(hh_wt_min['percent'], hh_wt_max['percent'], '%', dp=3)})",
    )
    print()
    _row(f'TV typical power (43–55" LED, indicative)  [28]', f"{TV_TYPICAL_WATTAGE} W")
    _row(
        "Usage-weighted energy → TV viewing",
        f"{_rng(wt_combined['total_energy_wh_min'], wt_combined['total_energy_wh_max'], 'Wh')}  →  {_rng(tv_wt_min['minutes'], tv_wt_max['minutes'], 'min')}",
    )
    print()

    # Appendix HW.3: cross-layer comparison
    c_train = car_displacement(training_co2e)
    f_train = flight_displacement(training_co2e)
    hw_train = homeworking_displacement(training_co2e)
    tv_train_co2e = tv_co2e_time(training_co2e)
    hh_train_co2e = household_co2e_time(training_co2e)
    c_meet = car_displacement(wt_combined["total_co2e_g"])
    f_meet = flight_displacement(wt_combined["total_co2e_g"])
    hw_meet = homeworking_displacement(wt_combined["total_co2e_g"])
    tv_meet_co2e = tv_co2e_time(wt_combined["total_co2e_g"])
    hh_meet_co2e = household_co2e_time(wt_combined["total_co2e_g"])
    c_aws = car_displacement(AWS_APR2026_CO2E_G)
    f_aws = flight_displacement(AWS_APR2026_CO2E_G)
    hw_aws = homeworking_displacement(AWS_APR2026_CO2E_G)
    tv_aws_co2e = tv_co2e_time(AWS_APR2026_CO2E_G)
    hh_aws_co2e = household_co2e_time(AWS_APR2026_CO2E_G)

    _section("Appendix HW.3: Cross-Layer Activity Comparison (unified CO₂e basis)")
    print("  All columns use CO₂e. TV/household: wattage × UK grid intensity (217 g/kWh).")
    print()
    w = 42
    print(
        f"  {'Cost layer':<{w}} {'CO₂e':>8}  {'Car':>8}  {'Flight':>10}  {'Homeworking':>13}  {'TV (100 W)':>12}  {'Household':>12}"
    )
    print(f"  {'-'*w} {'-'*8}  {'-'*8}  {'-'*10}  {'-'*13}  {'-'*12}  {'-'*12}")
    print(
        f"  {'LLM+ASR training, per user (proxy)':<{w}} {training_co2e:>6.1f} g  {c_train['metres']:>6.0f} m  {f_train['metres']:>8.0f} m  {hw_train['minutes']:>10.1f} min  {tv_train_co2e['minutes']:>9.1f} min  {hh_train_co2e['minutes']:>9.1f} min"
    )
    print(
        f"  {'Per-meeting AI inference (usage-wtd mid)':<{w}} {wt_combined['total_co2e_g']:>6.1f} g  {c_meet['metres']:>6.0f} m  {f_meet['metres']:>8.0f} m  {hw_meet['seconds']:>10.0f} s  {tv_meet_co2e['minutes']:>9.1f} min  {hh_meet_co2e['seconds']:>9.1f} s"
    )
    print(
        f"  {'Monthly AWS hosting (April 2026)':<{w}} {AWS_APR2026_CO2E_G:>5,} g  {c_aws['km']:>6.1f} km  {f_aws['pkm']:>8.1f} km  {hw_aws['working_days']:>9.1f} days  {tv_aws_co2e['hours']:>9.1f} h  {hh_aws_co2e['hours']:>9.1f} h"
    )
    print()
    ratio = AWS_APR2026_CO2E_G / wt_combined["total_co2e_g"]
    print(f"  Hosting : per-meeting ratio  {AWS_APR2026_CO2E_G:,} ÷ {wt_combined['total_co2e_g']:.1f} = {ratio:,.0f}×")
    print()


if __name__ == "__main__":
    display()
