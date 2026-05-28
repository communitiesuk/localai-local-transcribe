#!/usr/bin/env python3
"""
AWS Sustainability Carbon Emissions — Last Month Report.

Fetches actual AWS infrastructure carbon emissions for the previous calendar
month via the AWS CLI and contextualises them against the per-meeting modelled
impact from calculations.py.

Requirements:
  - AWS CLI installed and configured
  - Permissions for `aws sustainability get-estimated-carbon-emissions`

Run with:
  python documentation/env_assets/aws_carbon.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

# calculations.py lives next to this file; add its directory so it can be
# imported whether this script is run from the project root or anywhere else.
sys.path.insert(0, str(Path(__file__).parent))
from calculations import (  # noqa: E402
    HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR,
    NUM_SECTIONS,
    TRANSCRIPT_WORDS,
    WORKING_HOURS_PER_DAY,
    combined_impact,
    homeworking_displacement,
    transcription_impact,
    usage_weighted_impact,
)

_MTCO2E_TO_G = 1_000_000  # 1 MTCO2e = 1,000,000 g CO₂e
_MTCO2E_TO_KG = 1_000  # 1 MTCO2e = 1,000 kg CO₂e


# =============================================================================
# DATE HELPERS
# =============================================================================


def last_month_window() -> tuple[str, str, str]:
    """Return (start_iso, end_iso, human_label) for the previous calendar month.

    The AWS API uses an exclusive end date, so the end is the first day of the
    current month (not the last second of the previous one).
    """
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)
    label = last_month_start.strftime("%B %Y")
    return (
        last_month_start.strftime("%Y-%m-%dT00:00:00Z"),
        first_of_this_month.strftime("%Y-%m-%dT00:00:00Z"),
        label,
    )


# =============================================================================
# AWS SUSTAINABILITY API
# =============================================================================


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


# =============================================================================
# REPORTING HELPERS  (mirror the style in calculations.py)
# =============================================================================


def _section(title: str) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print("=" * 62)


def _row(label: str, value: str) -> None:
    print(f"  {label:<44} {value}")


# =============================================================================
# MAIN REPORT
# =============================================================================


def print_report() -> None:
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

    # ── Raw AWS figures ───────────────────────────────────────────────────────
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

    # ── AI processing cost per hour of meeting (from calculations.py) ─────────
    asr = transcription_impact()
    wt = usage_weighted_impact(TRANSCRIPT_WORDS, NUM_SECTIONS)
    wt_combined = combined_impact(wt, asr)
    per_hour_g = wt_combined["total_co2e_g"]

    _section("AI Processing Cost — per 1-hour meeting  [from calculations.py]")
    _row(
        "Usage-weighted CO₂e / hour",
        f"{per_hour_g:.1f} g CO₂e",
    )
    _row("Scope", "Transcription (ASR) + LLM inference, EU-27 grid intensity")

    # ── Contextualisation ─────────────────────────────────────────────────────
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
        print(f"    of a single 1-hour meeting (MBM, market-adjusted basis).")
        print()
        print("  ⚠  AWS figure = all account services (EC2, RDS, S3, networking, …).")
        print("  AI figure = transcription + LLM inference on Azure/OpenAI — different layer.")
        print("  Together they represent the two distinct slices of total system footprint.")

    # ── Homeworking displacement ──────────────────────────────────────────────
    hw_meeting = homeworking_displacement(per_hour_g)
    hw_hosting_mbm = homeworking_displacement(mbm_g)

    _section(f"Homeworking Displacement  [UK GHG CF 2025] — {label}")
    print("  Source: UK Government GHG Conversion Factors 2025 (DESNZ/DEFRA)")
    print("  https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025")
    print(f"  Rate: {HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour")
    print(f"        (office equipment 0.03144 + heating 0.30234, Scope 1+2)")
    print()
    print("  ─── One 1-hour meeting — AI processing only ───────────────────────")
    _row("Meeting AI CO₂e (usage-weighted)", f"{per_hour_g:.2f} g CO₂e")
    _row(
        "≡ homeworking",
        f"{hw_meeting['seconds']:.1f} s  "
        f"({hw_meeting['minutes']:.3f} min  /  {hw_meeting['hours']:.5f} h)",
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
    print_report()
