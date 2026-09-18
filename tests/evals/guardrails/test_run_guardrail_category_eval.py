from pathlib import Path

from common.types import FailureCategory
from evals.guardrails.src.run_guardrail_category_eval import _build_stdout_summary, _score_requested_metrics


def test_score_requested_metrics_include_category_and_no_issue_f1() -> None:
    results = [
        {
            "expected_categories": [FailureCategory.FACTUAL_INTEGRITY.name],
            "predicted_categories": [FailureCategory.FACTUAL_INTEGRITY.name],
            "score": 0.0,
        },
        {
            "expected_categories": [],
            "predicted_categories": [],
            "score": 1.0,
        },
    ]

    metrics = _score_requested_metrics(results)

    assert metrics["f1_overall"] == 1.0
    assert metrics["f1_factual_integrity"] == 1.0
    assert metrics["f1_no_issue"] == 1.0


def test_build_stdout_summary_uses_requested_f1_metric_names() -> None:
    report = {
        "metrics": {
            "f1_overall": 0.75,
            "f1_factual_integrity": 0.5,
            "f1_required_content_and_structure": 0.0,
            "f1_edit_safety_and_intent": 0.0,
            "f1_data_protection": 0.0,
            "f1_instruction_integrity": 0.0,
            "f1_evidence_and_citation_quality": 0.0,
            "f1_no_issue": 1.0,
        }
    }

    summary = _build_stdout_summary(report, Path("evals/guardrails/output/results.json"))

    assert summary == {
        "f1_overall": 0.75,
        "f1_factual_integrity": 0.5,
        "f1_required_content_and_structure": 0.0,
        "f1_edit_safety_and_intent": 0.0,
        "f1_data_protection": 0.0,
        "f1_instruction_integrity": 0.0,
        "f1_evidence_and_citation_quality": 0.0,
        "f1_no_issue": 1.0,
        "output": "evals/guardrails/output/results.json",
    }
