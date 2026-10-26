import os
from pathlib import Path

import httpx
import pytest

from reporting.aggregate_analytics.caseload import load_caseload
from reporting.aggregate_analytics.measures import Count
from reporting.aggregate_analytics.report import (
    Sources,
    load_env,
    missing_env,
    months_in_range,
    report_folder_name,
    run_all,
    slugify,
    write_csv_reports,
    write_report,
)
from reporting.aggregate_analytics.sources import plausible_monthly_counts


def test_missing_env_lists_unset_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAUSIBLE_BASE_URL", "https://example.test")
    monkeypatch.delenv("PLAUSIBLE_SITE_ID", raising=False)
    monkeypatch.setenv("PLAUSIBLE_API_KEY", "")
    assert missing_env() == ["PLAUSIBLE_SITE_ID", "PLAUSIBLE_API_KEY"]


def test_write_report_creates_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "missing" / "output"
    path = write_report([{"measure": "m", "rows": []}], "r.json", out_dir)
    assert path == out_dir / "r.json"
    assert '"measure": "m"' in path.read_text()


def test_write_report_rejects_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="file name"):
        write_report([], "../escape.json", tmp_path)


def test_report_folder_name() -> None:
    assert report_folder_name("2026-09-01", "2026-09-30") == "2026-09-01_to_2026-09-30"


def test_slugify() -> None:
    assert slugify("Audio uploads per live recording start") == "audio_uploads_per_live_recording_start"


def test_write_csv_reports_creates_one_file_per_measure(tmp_path: Path) -> None:
    out_dir = tmp_path / "missing" / "output"
    report = [
        {"measure": "Ratio measure", "rows": [{"numerator (a)": 5, "denominator (b)": 10, "percentage": 50.0}]},
        {"measure": "Monthly measure", "rows": [{"month": "2026-09", "count": 3}]},
    ]

    paths = write_csv_reports(report, out_dir)

    assert paths == [out_dir / "ratio_measure.csv", out_dir / "monthly_measure.csv"]
    assert (out_dir / "ratio_measure.csv").read_text() == "numerator (a),denominator (b),percentage\n5,10,50.0\n"
    assert (out_dir / "monthly_measure.csv").read_text() == "month,count\n2026-09,3\n"


def test_write_csv_reports_handles_empty_rows(tmp_path: Path) -> None:
    paths = write_csv_reports([{"measure": "Empty measure", "rows": []}], tmp_path)

    assert (tmp_path / "empty_measure.csv").read_text() == ""
    assert paths == [tmp_path / "empty_measure.csv"]


ORG_A = "11111111-1111-1111-1111-111111111111"
ORG_B = "22222222-2222-2222-2222-222222222222"

COUNTS = {
    ("plausible", "live_recording_started", None): 200,
    ("plausible", "audio_upload_complete_from_live_recording", None): 150,
    ("plausible", "transcript_requested_for_live_recording", None): 100,
    ("postgres", "TRANSCRIPTION_RECEIVED", "live_recording"): 80,
    ("postgres", "TRANSCRIPTION_RECEIVED", None): 160,
    ("plausible", "summary_requested", None): 120,
    ("postgres", "SUMMARY_RECEIVED", None): 40,
}


def fake_count(count: Count, _start: str, _end: str) -> int:
    return COUNTS.get((count.source, count.event, count.recording_source), 0)


def fake_monthly_counts(source: str, events: tuple[str, ...], _start: str, _end: str, *, by_organisation: bool) -> dict:
    if source == "plausible":
        assert events == ("audio_upload_complete_from_live_recording", "audio_upload_complete_from_direct_upload")
        return {(ORG_A, "2026-09"): 30, (ORG_B, "2026-09"): 5}
    if by_organisation:
        return {(ORG_A, "2026-09"): 10, (ORG_A, "2026-10"): 4}
    return {(None, "2026-09"): 40}


def test_plausible_monthly_counts_parses_organisation_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAUSIBLE_BASE_URL", "https://plausible.test")
    monkeypatch.setenv("PLAUSIBLE_API_KEY", "key")
    monkeypatch.setenv("PLAUSIBLE_SITE_ID", "site")
    captured = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        captured.update(url=url, **kwargs)
        body = {
            "results": [
                {"dimensions": ["2026-09-01", ORG_A.upper()], "metrics": [30]},
                {"dimensions": ["2026-09-01", "(none)"], "metrics": [2]},
            ]
        }
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)

    counts = plausible_monthly_counts(("a", "b"), "2026-09-01", "2026-09-30", by_organisation=True)

    assert counts == {(ORG_A, "2026-09"): 30, (None, "2026-09"): 2}
    assert captured["json"]["dimensions"] == ["time:month", "event:props:organisation_id"]
    assert captured["json"]["filters"] == [["is", "event:name", ["a", "b"]]]


def results(sources: Sources) -> dict[str, list]:
    return {r["measure"]: r["rows"] for r in run_all("2026-09-01", "2026-10-31", sources)}


@pytest.fixture
def sources() -> Sources:
    return Sources(
        count=fake_count,
        monthly_counts=fake_monthly_counts,
        caseload={(ORG_A, "2026-09"): 60, (ORG_A, "2026-10"): 50, (ORG_B, "2026-10"): 20, (ORG_B, "2025-01"): 99},
    )


def test_ratio_measures(sources: Sources) -> None:
    out = results(sources)

    assert out["Audio uploads per live recording start"] == [
        {
            "numerator (audio_upload_complete_from_live_recording)": 150,
            "denominator (live_recording_started)": 200,
            "percentage": 75.0,
        }
    ]
    assert out["Transcription requests per live recording start"][0]["percentage"] == 50.0
    assert out["Transcription receipts per live recording start"] == [
        {
            "numerator (TRANSCRIPTION_RECEIVED, live_recording)": 80,
            "denominator (live_recording_started)": 200,
            "percentage": 40.0,
        }
    ]
    assert out["Summary requests per transcript received"] == [
        {
            "numerator (summary_requested)": 120,
            "denominator (TRANSCRIPTION_RECEIVED)": 160,
            "percentage": 75.0,
        }
    ]
    assert out["Summary receipts per transcript received"] == [
        {
            "numerator (SUMMARY_RECEIVED)": 40,
            "denominator (TRANSCRIPTION_RECEIVED)": 160,
            "percentage": 25.0,
        }
    ]


def test_ratio_percentage_is_none_when_denominator_is_zero() -> None:
    out = results(Sources(count=lambda *_: 0, monthly_counts=fake_monthly_counts))

    assert out["Audio uploads per live recording start"][0]["percentage"] is None


def test_audio_uploads_versus_caseload_has_row_per_organisation_and_month(sources: Sources) -> None:
    rows = results(sources)["Audio uploads versus estimated organisation caseload"]

    assert rows == [
        {"organisation_id": ORG_A, "month": "2026-09", "count": 30, "estimated_caseload": 60, "percentage": 50.0},
        {"organisation_id": ORG_B, "month": "2026-09", "count": 5, "estimated_caseload": None, "percentage": None},
        {"organisation_id": ORG_A, "month": "2026-10", "count": 0, "estimated_caseload": 50, "percentage": 0.0},
        {"organisation_id": ORG_B, "month": "2026-10", "count": 0, "estimated_caseload": 20, "percentage": 0.0},
    ]


def test_summaries_versus_caseload(sources: Sources) -> None:
    rows = results(sources)["Summaries versus estimated caseload"]

    assert rows[0] == {
        "organisation_id": ORG_A,
        "month": "2026-09",
        "count": 10,
        "estimated_caseload": 60,
        "percentage": 16.67,
    }


def test_caseload_measures_without_caseload_dataset() -> None:
    rows = results(Sources(count=fake_count, monthly_counts=fake_monthly_counts))["Summaries versus estimated caseload"]

    assert all(row["estimated_caseload"] is None and row["percentage"] is None for row in rows)
    assert [row["count"] for row in rows] == [10, 4]


def test_load_env_ignores_unrelated_variables_such_as_aws_keys(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("AWS_ACCESS_KEY_ID=placeholder\nPLAUSIBLE_SITE_ID=site\nPOSTGRES_HOST=db\n")
    for name in ("AWS_ACCESS_KEY_ID", "PLAUSIBLE_SITE_ID", "POSTGRES_HOST"):
        monkeypatch.delenv(name, raising=False)

    try:
        load_env([env_file])

        assert "AWS_ACCESS_KEY_ID" not in os.environ
        assert "POSTGRES_HOST" not in os.environ
        assert os.environ["PLAUSIBLE_SITE_ID"] == "site"
    finally:
        os.environ.pop("PLAUSIBLE_SITE_ID", None)


def test_months_in_range_spans_year_end() -> None:
    assert months_in_range("2026-11-15", "2027-01-02") == ["2026-11", "2026-12", "2027-01"]


def test_load_caseload(tmp_path: Path) -> None:
    path = tmp_path / "caseload.csv"
    path.write_text(f"organisation_id,month,estimated_caseload\n{ORG_A.upper()},2026-09,60\n")

    assert load_caseload(path) == {(ORG_A, "2026-09"): 60}


def test_load_caseload_rejects_duplicates_and_bad_months(tmp_path: Path) -> None:
    duplicate = tmp_path / "dup.csv"
    duplicate.write_text(f"organisation_id,month,estimated_caseload\n{ORG_A},2026-09,1\n{ORG_A},2026-09,2\n")
    bad_month = tmp_path / "bad.csv"
    bad_month.write_text(f"organisation_id,month,estimated_caseload\n{ORG_A},09/2026,1\n")
    missing = tmp_path / "missing.csv"
    missing.write_text("organisation_id,month\n")

    for path in (duplicate, bad_month, missing):
        with pytest.raises(ValueError):  # noqa: PT011
            load_caseload(path)
