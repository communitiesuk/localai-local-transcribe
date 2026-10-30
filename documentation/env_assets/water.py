"""Section 4.2 + Appendix H: Scope 2 water embedded in purchased electricity.

Applies the WRI grid-average water use factors [29] to the energy (kWh) already
computed for each component, giving water withdrawal and consumption per
1-hour meeting and per user (training). Inference is UK-hosted (GB factors);
training runs on the US grid (US factors). Scope 1 (on-site cooling) is small
for the providers used and reported separately by operators (§4.1).
"""

from utils import (
    AWS_APR2026_LBM_CO2E_G,
    LLM_CARBON_INTENSITY_G_PER_KWH,
    WATER_GB_CONSUMPTION_GAL_PER_KWH,
    WATER_GB_CONSUMPTION_L_PER_KWH,
    WATER_GB_WITHDRAWAL_GAL_PER_KWH,
    WATER_GB_WITHDRAWAL_L_PER_KWH,
    WATER_US_CONSUMPTION_GAL_PER_KWH,
    WATER_US_CONSUMPTION_L_PER_KWH,
    WATER_US_WITHDRAWAL_GAL_PER_KWH,
    WATER_US_WITHDRAWAL_L_PER_KWH,
    combined_impact,
    scope2_water,
    _ml,
    _row,
    _section,
)


def _vol(litres: float) -> str:
    """Human volume: mL below 1 L, L below 1000 L, else L with hectolitre hint."""
    if abs(litres) < 1:
        return f"{litres * 1_000:.1f} mL"
    if abs(litres) < 1_000:
        return f"{litres:.2f} L"
    return f"{litres:,.0f} L ({litres / 100:,.0f} hL)"


def _band(energy_wh_min: float, energy_wh_max: float, grid: str = "gb") -> dict:
    """Water for an energy band on a given grid, plus its midpoint."""
    lo = scope2_water(energy_wh_min, grid)
    hi = scope2_water(energy_wh_max, grid)
    return {
        "withdrawal_l_min": lo["withdrawal_l"],
        "withdrawal_l_max": hi["withdrawal_l"],
        "consumption_l_min": lo["consumption_l"],
        "consumption_l_max": hi["consumption_l"],
        "withdrawal_l_mid": (lo["withdrawal_l"] + hi["withdrawal_l"]) / 2,
        "consumption_l_mid": (lo["consumption_l"] + hi["consumption_l"]) / 2,
    }


def _aws_lbm() -> tuple[float, str, bool]:
    """Latest-month AWS location-based CO₂e (g), with offline fallback to the snapshot.

    Returns (lbm_g, month_label, is_live). Falls back to the recorded April 2026
    snapshot when AWS credentials are unavailable so the report still runs.
    """
    import aws

    try:
        a = aws.calculate()
    except RuntimeError:
        return float(AWS_APR2026_LBM_CO2E_G), "April 2026 (snapshot)", False
    return a["lbm_g"], a["label"], True


def calculate() -> dict:
    import llm_inference
    import training
    import transcription

    asr = transcription.calculate()
    llm = llm_inference.calculate()
    training_r = training.calculate()

    wt_combined = combined_impact(llm["usage_weighted"], asr)
    training_wh = training_r["llm"]["llm_total_wh"] + training_r["asr"]["per_user_wh"]

    # AWS reports carbon, not energy. Pull the latest available month's
    # location-based (LBM) figure live, then recover kWh by dividing through the
    # GB grid intensity. LBM uses grid averages, so it reverses cleanly.
    lbm_g, aws_label, aws_live = _aws_lbm()
    aws_kwh = lbm_g / LLM_CARBON_INTENSITY_G_PER_KWH
    aws_band = _band(aws_kwh * 1_000, aws_kwh * 1_000)
    aws_band.update(kwh=aws_kwh, lbm_g=lbm_g, label=aws_label, live=aws_live)

    return {
        # Inference (ASR + LLM) is UK-hosted → GB factors.
        "asr": _band(asr["energy_wh"], asr["energy_wh"]),
        "llm_usage_weighted": _band(llm["usage_weighted"]["total_wh_min"], llm["usage_weighted"]["total_wh_max"]),
        "combined_per_meeting": _band(wt_combined["total_energy_wh_min"], wt_combined["total_energy_wh_max"]),
        # Training runs on the US grid → US factors.
        "training_per_user": _band(training_wh, training_wh, grid="us"),
        # AWS hosting is UK-hosted → GB factors.
        "aws_monthly": aws_band,
    }


def _w(band: dict) -> str:
    """Withdrawal range as a string."""
    return f"{_ml(band['withdrawal_l_min'])} – {_ml(band['withdrawal_l_max'])}"


def _c(band: dict) -> str:
    """Consumption range as a string."""
    return f"{_ml(band['consumption_l_min'])} – {_ml(band['consumption_l_max'])}"


def display() -> None:
    r = calculate()

    _section("Appendix H: Scope 2 Water — Factors [WRI]")
    print(f"  {'Grid':<26} {'Withdrawal':>22} {'Consumption':>20}")
    print(f"  {'-'*26} {'-'*22} {'-'*20}")
    print(
        f"  {'Great Britain (inference)':<26}"
        f" {f'{WATER_GB_WITHDRAWAL_GAL_PER_KWH} gal = {WATER_GB_WITHDRAWAL_L_PER_KWH:.2f} L':>22}"
        f" {f'{WATER_GB_CONSUMPTION_GAL_PER_KWH} gal = {WATER_GB_CONSUMPTION_L_PER_KWH:.2f} L':>20}"
    )
    print(
        f"  {'United States (training)':<26}"
        f" {f'{WATER_US_WITHDRAWAL_GAL_PER_KWH} gal = {WATER_US_WITHDRAWAL_L_PER_KWH:.2f} L':>22}"
        f" {f'{WATER_US_CONSUMPTION_GAL_PER_KWH} gal = {WATER_US_CONSUMPTION_L_PER_KWH:.2f} L':>20}"
    )
    print("  (per kWh; 1 US gallon = 3.785411784 L.)")

    _section("Section 4.2: Scope 2 Water per 1-Hour Meeting (GB grid)")
    print(f"  {'Component':<34} {'Withdrawal':>22} {'Consumption':>22}")
    print(f"  {'-'*34} {'-'*22} {'-'*22}")
    asr, llm_wt, comb = r["asr"], r["llm_usage_weighted"], r["combined_per_meeting"]
    print(f"  {'Transcription (ASR)':<34} {_ml(asr['withdrawal_l_mid']):>22} {_ml(asr['consumption_l_mid']):>22}")
    print(f"  {'LLM inference (usage-weighted)':<34} {_w(llm_wt):>22} {_c(llm_wt):>22}")
    print(f"  {'Combined (ASR + LLM)':<34} {_w(comb):>22} {_c(comb):>22}")
    print()
    _row("Combined withdrawal (midpoint)", _ml(comb["withdrawal_l_mid"]))
    _row("Combined consumption (midpoint)", _ml(comb["consumption_l_mid"]))

    aws = r["aws_monthly"]
    source = "live" if aws["live"] else "snapshot — no AWS credentials"
    _section(f"Section 4.2: Scope 2 Water — AWS Hosting ({aws['label']}, GB grid) [{source}]")
    _row(
        "Energy recovered from LBM",
        f"{aws['lbm_g']:,.0f} g CO₂e / {LLM_CARBON_INTENSITY_G_PER_KWH:.1f} g/kWh  = {aws['kwh']:,.0f} kWh",
    )
    _row("Withdrawal", _vol(aws["withdrawal_l_mid"]))
    _row("Consumption", _vol(aws["consumption_l_mid"]))

    tr = r["training_per_user"]
    _section("Section 4.2: Combined View — Scope 2 Water by Layer")
    print(f"  {'Layer':<34} {'Basis':<20} {'Withdrawal':>20} {'Consumption':>16}")
    print(f"  {'-'*34} {'-'*20} {'-'*20} {'-'*16}")
    for label, basis, band in [
        ("AI processing (ASR + LLM)", "per 1-h meeting", comb),
        ("Model training", "per user, one-off", tr),
        ("AWS hosting", f"per month ({aws['label'].split(' (')[0]})", aws),
    ]:
        print(f"  {label:<34} {basis:<20} {_vol(band['withdrawal_l_mid']):>20} {_vol(band['consumption_l_mid']):>16}")

    _section("Appendix H: Scope 2 Water — Training (per user, amortised, US grid)")
    _row("Withdrawal", _ml(tr["withdrawal_l_mid"]))
    _row("Consumption", _ml(tr["consumption_l_mid"]))
    print()


if __name__ == "__main__":
    display()
