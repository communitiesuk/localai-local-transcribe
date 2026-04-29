from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast

import pytest

from evals.summarisation.src.hallucination.types import (
    ClassifiedStatement,
    HallucinationInput,
    HallucinationReport,
    SupportLabel,
)


def test_classified_statement_valid_labels():
    labels: tuple[SupportLabel, ...] = ("Supported", "Unsupported", "Partial")
    for label in labels:
        stmt = ClassifiedStatement(
            hallucination_text="x",
            citation_indices=[],
            hallucination_type=label,
            hallucination_reason="r",
        )
        assert stmt.hallucination_type == label


def test_classified_statement_invalid_label_rejected():
    with pytest.raises(ValueError, match="Input should be"):
        ClassifiedStatement(
            hallucination_text="x",
            citation_indices=[],
            hallucination_type=cast(SupportLabel, "Invalid"),
            hallucination_reason="r",
        )


def test_hallucination_report_serialises_to_json():
    report = HallucinationReport(
        run_id="run-abc",
        example_id="test-001",
        hypothesis_model="gpt-4o",
        template_name="General",
        timestamp=datetime.now(UTC),
        prompt_version="v1",
        statements=[
            ClassifiedStatement(
                hallucination_text="The unicorn Sparklehoof was mentioned",
                citation_indices=[],
                hallucination_type="Unsupported",
                hallucination_reason="Could not find supporting evidence in the transcript",
            ),
        ],
        metrics={"n_hallucinations": 1, "n_supported": 4, "hallucination_rate": 0.2, "no_hallucinations": False},
    )

    serialised = report.model_dump(mode="json")
    json_str = json.dumps(serialised)
    data = json.loads(json_str)

    assert data["example_id"] == "test-001"
    assert data["hypothesis_model"] == "gpt-4o"
    assert data["run_id"] == "run-abc"
    assert data["metrics"]["n_hallucinations"] == 1
    assert data["metrics"]["n_supported"] == 4
    assert data["metrics"]["hallucination_rate"] == 0.2
    assert data["metrics"]["no_hallucinations"] is False
    assert len(data["statements"]) == 1


def test_hallucination_report_no_hallucinations_flag():
    report = HallucinationReport(
        run_id="run-xyz",
        example_id="empty",
        hypothesis_model="gpt-4o",
        template_name=None,
        timestamp=datetime.now(UTC),
        prompt_version="dev",
        statements=[],
        metrics={"n_hallucinations": 0, "n_supported": 0, "hallucination_rate": 0.0, "no_hallucinations": True},
    )
    assert report.metrics["no_hallucinations"] is True


def test_hallucination_input_roundtrips():
    data = {
        "example_id": "abc",
        "hypothesis_model": "gpt-4o",
        "summary_html": "<p>Summary [1]</p>",
        "uncited_claims": ["The unicorn Sparklehoof was mentioned"],
    }
    inp = HallucinationInput.model_validate(data)
    assert inp.example_id == "abc"
    assert inp.summary_html == "<p>Summary [1]</p>"
    assert inp.uncited_claims == ["The unicorn Sparklehoof was mentioned"]


def test_hallucination_input_uncited_claims_defaults_empty():
    inp = HallucinationInput.model_validate(
        {
            "example_id": "abc",
            "hypothesis_model": "gpt-4o",
            "summary_html": "Summary text",
        }
    )
    assert inp.uncited_claims == []
