"""AWS monthly carbon report from manual input or the Sustainability API."""

import argparse
import json
import math
import subprocess
from datetime import date, timedelta

from utils import (
    HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR,
    NUM_SECTIONS,
    TRANSCRIPT_WORDS,
    WORKING_HOURS_PER_DAY,
    _row,
    _section,
    combined_impact,
)

_MTCO2E_TO_G = 1_000_000
_MTCO2E_TO_KG = 1_000


def last_month_window() -> tuple[str, str, str]:
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)
    return (
        last_month_start.strftime("%Y-%m-%dT00:00:00Z"),
        first_of_this_month.strftime("%Y-%m-%dT00:00:00Z"),
        last_month_start.strftime("%B %Y"),
    )


def fetch_aws_emissions(start: str, end: str) -> dict:
    try:
        proc = subprocess.run(
            [
                "aws",
                "sustainability",
                "get-estimated-carbon-emissions",
                "--time-period",
                json.dumps({"Start": start, "End": end}),
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
    results = json.loads(proc.stdout).get("Results", [])
    if not results:
        msg = "AWS Sustainability API returned no results for the requested period."
        raise RuntimeError(msg)
    return results[0]


def prompt_for_aws_emissions() -> dict:
    """Collect last month's AWS carbon emissions from the AWS Console."""

    print("\nOpen the AWS Sustainability page in the AWS Console.")
    print("Find the latest month's carbon footprint and enter these two values.")

    emissions = {}
    for key, label in [
        ("TOTAL_MBM_CARBON_EMISSIONS", "Market-based emissions (MTCO2e)"),
        ("TOTAL_LBM_CARBON_EMISSIONS", "Location-based emissions (MTCO2e)"),
    ]:
        while True:
            raw_value = input(f"  {label}: ")
            try:
                value = float(raw_value)
            except ValueError:
                print("  Enter a number, for example 0.017317.")
                continue
            if value < 0 or not math.isfinite(value):
                print("  Enter a finite value greater than or equal to zero.")
                continue
            emissions[key] = {"Value": value}
            break

    return {
        "EmissionsValues": emissions,
        "ModelVersion": "manual console entry",
    }


def calculate(*, api_calls: bool = False) -> dict:
    """Get last month's AWS carbon emissions, using manual input by default."""
    start, end, label = last_month_window()
    result = fetch_aws_emissions(start, end) if api_calls else prompt_for_aws_emissions()
    emissions = result["EmissionsValues"]
    mbm_mtco2e: float = emissions["TOTAL_MBM_CARBON_EMISSIONS"]["Value"]
    lbm_mtco2e: float = emissions["TOTAL_LBM_CARBON_EMISSIONS"]["Value"]
    return {
        "start": start,
        "end": end,
        "label": label,
        "model_version": result.get("ModelVersion", "unknown"),
        "source": "AWS API via CLI" if api_calls else "manual console entry",
        "mbm_g": mbm_mtco2e * _MTCO2E_TO_G,
        "mbm_kg": mbm_mtco2e * _MTCO2E_TO_KG,
        "mbm_mtco2e": mbm_mtco2e,
        "lbm_g": lbm_mtco2e * _MTCO2E_TO_G,
        "lbm_kg": lbm_mtco2e * _MTCO2E_TO_KG,
        "lbm_mtco2e": lbm_mtco2e,
    }


def display(aws_data: dict | None = None, *, api_calls: bool = False) -> None:
    import llm_inference
    import transcription

    aws = aws_data or calculate(api_calls=api_calls)
    mbm_g, lbm_g = aws["mbm_g"], aws["lbm_g"]
    label = aws["label"]

    print(f"\nAWS INFRASTRUCTURE CARBON EMISSIONS — {label}")
    print(f"  Source: {aws['source']}")

    _section(f"AWS Sustainability API — {label}  [model {aws['model_version']}]")
    _row("Period", f"{aws['start'][:10]} – {aws['end'][:10]}")
    _row(
        "Market-based    (MBM) ★ primary",
        f"{aws['mbm_mtco2e']:.6f} MTCO2e  =  {aws['mbm_kg']:.3f} kg  =  {mbm_g:,.0f} g CO₂e",
    )
    _row(
        "Location-based  (LBM) reference",
        f"{aws['lbm_mtco2e']:.6f} MTCO2e  =  {aws['lbm_kg']:.3f} kg  =  {lbm_g:,.0f} g CO₂e",
    )
    print()
    print("  MBM  subtracts renewable-energy certificates (RECs) purchased by AWS.")
    print("  LBM  uses regional grid averages (shown for reference).")

    asr = transcription.calculate()
    llm = llm_inference.calculate(TRANSCRIPT_WORDS, NUM_SECTIONS)
    wt_combined = combined_impact(llm["usage_weighted"], asr)
    per_hour_g = wt_combined["total_co2e_g"]

    _section("AI Processing Cost — per 1-hour meeting")
    _row("Usage-weighted CO₂e / hour", f"{per_hour_g:.1f} g CO₂e")
    _row("Scope", "Transcription (ASR) + LLM inference, UK GBR grid")

    if per_hour_g > 0:
        mbm_eq = mbm_g / per_hour_g
        _section(f"Context — {label} AWS infra vs. per-meeting AI cost")
        _row("MBM ÷ AI cost per hour", f"{mbm_g:,.0f} g ÷ {per_hour_g:.1f} g  ≈  {mbm_eq:,.0f} hours of AI processing")
        _row(
            "LBM ÷ AI cost per hour (ref)",
            f"{lbm_g:,.0f} g ÷ {per_hour_g:.1f} g  ≈  {lbm_g / per_hour_g:,.0f} hours of AI processing",
        )
        print()
        print(f"  → {label} AWS hosting emitted ~{mbm_eq:,.0f}× the AI cost of a single 1-hour meeting.")
        print()
        print("  ⚠  AWS figure = all account services (EC2, RDS, S3, networking, …).")
        print("  AI figure = transcription + LLM inference on Azure/OpenAI — different layer.")

    hw_g_per_hour = HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR * 1_000
    hw_meeting_h = per_hour_g / hw_g_per_hour
    hw_hosting_h = mbm_g / hw_g_per_hour

    _section(f"Homeworking Displacement — {label}")
    print(f"  Rate: {HOMEWORKING_TOTAL_KG_CO2E_PER_HOUR} kg CO₂e / FTE working hour  [UK GHG CF 2025]")
    print()
    _row("Meeting AI CO₂e (usage-weighted)", f"{per_hour_g:.2f} g CO₂e")
    _row("≡ homeworking", f"{hw_meeting_h * 3_600:.1f} s  ({hw_meeting_h * 60:.3f} min)")
    print()
    _row("Monthly hosting CO₂e (MBM)", f"{mbm_g:,.0f} g  ({aws['mbm_kg']:.3f} kg)")
    _row(
        "≡ homeworking",
        f"{hw_hosting_h:,.1f} h  ({hw_hosting_h / WORKING_HOURS_PER_DAY:,.1f} working day(s) at {WORKING_HOURS_PER_DAY} h/day)",
    )
    print()
    if hw_meeting_h > 0:
        print(
            f"  → Monthly AWS hosting is ~{hw_hosting_h / hw_meeting_h:,.0f}× more carbon-intensive than one meeting."
        )
        print("  Conclusion: right-sizing or switching off idle AWS resources delivers far greater")
        print("  carbon savings than optimising AI prompt length.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api_calls",
        action="store_true",
        help="Use AWS API calls for development/staging only. DO NOT use for production.",
    )
    args = parser.parse_args()
    display(api_calls=args.api_calls)
