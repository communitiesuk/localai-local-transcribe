from pathlib import Path

from common.types import FailureCategory, FailureDetail, FailureMode, GuardrailScore
from evals.guardrails.src.run_guardrail_category_eval import (
    _apply_mutations,
    _build_stdout_summary,
    _score_requested_metrics,
)


def test_apply_mutations_remove_between_removes_end_marker() -> None:
    result = _apply_mutations(
        "before START remove me END after",
        [{"type": "remove_between", "start": "START", "end": "END"}],
    )

    assert result == "before  after"


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
    assert "f1_required_content_and_structure" not in metrics
    assert "f1_edit_safety_and_intent" not in metrics


def test_build_stdout_summary_uses_requested_f1_metric_names() -> None:
    output_path = Path("evals/guardrails/output/results.json")
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

    summary = _build_stdout_summary(report, output_path)

    assert summary == {
        "f1_overall": 0.75,
        "f1_factual_integrity": 0.5,
        "f1_required_content_and_structure": 0.0,
        "f1_edit_safety_and_intent": 0.0,
        "f1_data_protection": 0.0,
        "f1_instruction_integrity": 0.0,
        "f1_evidence_and_citation_quality": 0.0,
        "f1_no_issue": 1.0,
        "output": str(output_path),
    }


def test_failure_detail_dump_includes_derived_category() -> None:
    score = GuardrailScore(
        score=0.0,
        reasoning="Found invented decision",
        categories=[FailureDetail(mode=FailureMode.INVENTED_DECISION, explanation="Approval was invented.")],
    )

    assert [detail.model_dump(mode="json") for detail in score.categories] == [
        {
            "mode": FailureMode.INVENTED_DECISION.value,
            "explanation": "Approval was invented.",
            "category": FailureCategory.FACTUAL_INTEGRITY.value,
        }
    ]
