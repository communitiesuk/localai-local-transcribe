import pytest
import asyncio
from types import SimpleNamespace

from evals.summarisation.src.common.metric import DialogSummaryMetric, MetricResult
from evals.summarisation.src.common.schemas import DialogExample

# Helper to create a dummy prediction object expected by the metric
class DummyPrediction:
    def __init__(self, summary: str):
        self.summary = summary

# Mock response generator for the async LLM judge call
async def _mock_call_llm_judge_success(system: str, user: str):
    # Return a structure matching the expected RubricEvaluation
    return {
        "dimensions": {
            "accuracy": {"score": 5, "rationale": "Excellent factual consistency"}
        }
    }

async def _mock_call_llm_judge_fallback(system: str, user: str):
    # Return a dict where the requested dimension is missing, forcing the fallback to the first key
    return {
        "dimensions": {
            "some_other": {"score": 3, "rationale": "Adequate but not perfect"}
        }
    }

async def _mock_call_llm_judge_missing(system: str, user: str):
    # Return an empty dimensions dict to trigger the default missing handling
    return {"dimensions": {}}

@pytest.fixture(autouse=True)
def patch_llm_calls(monkeypatch):
    """Patch the LLM judge call with a default successful mock.
    Individual tests can override this fixture by monkeypatching again.
    """
    monkeypatch.setattr(
        "evals.summarisation.src.common.metric.call_llm_judge",
        _mock_call_llm_judge_success,
    )
    yield

def test_dialog_summary_metric_evaluate_success(monkeypatch):
    """Metric should return a scaled score (0-1) and a detailed reason string.

    The LLM judge mock returns a score of 5 for the "accuracy" dimension, which
    maps directly to a scaled score of 1.0.
    """
    # Ensure the success mock is used (explicit, though fixture already does this)
    monkeypatch.setattr(
        "evals.summarisation.src.common.metric.call_llm_judge",
        _mock_call_llm_judge_success,
    )

    metric = DialogSummaryMetric(name="rubric_faithfulness", criterion="faithfulness", pass_threshold=4)
    example = DialogExample(example_id="ex1", dialogue="User says hello.", reference_summary="Hello.")
    prediction = DummyPrediction(summary="Hello.")

    result: MetricResult = metric.evaluate(example=example, prediction=prediction)

    # Score is scaled: (5-1)/4 = 1.0
    assert pytest.approx(result.score, 0.001) == 1.0
    assert "rubric_accuracy_score=5" in result.reason
    assert "Excellent factual consistency" in result.reason

def test_dialog_summary_metric_fallback_to_first_dimension(monkeypatch):
    """When the requested dimension is missing, the metric should fall back to the first available dimension.
    """
    monkeypatch.setattr(
        "evals.summarisation.src.common.metric.call_llm_judge",
        _mock_call_llm_judge_fallback,
    )
    metric = DialogSummaryMetric(name="rubric_faithfulness", criterion="faithfulness", pass_threshold=4)
    example = DialogExample(example_id="ex2", dialogue="User asks a question.", reference_summary="Answer.")
    prediction = DummyPrediction(summary="Answer.")

    result: MetricResult = metric.evaluate(example=example, prediction=prediction)

    # The fallback uses the first key ("some_other") with score 3 -> scaled (3-1)/4 = 0.5
    assert pytest.approx(result.score, 0.001) == 0.5
    assert "rubric_some_other_score=3" in result.reason
    assert "Adequate but not perfect" in result.reason

def test_dialog_summary_metric_missing_dimensions_returns_zero(monkeypatch):
    """If the LLM judge returns no dimensions, the metric should default to the lowest score (0 after scaling)."""
    monkeypatch.setattr(
        "evals.summarisation.src.common.metric.call_llm_judge",
        _mock_call_llm_judge_missing,
    )
    metric = DialogSummaryMetric(name="rubric_faithfulness", criterion="faithfulness", pass_threshold=4)
    example = DialogExample(example_id="ex3", dialogue="User dialogue.", reference_summary="Summary.")
    prediction = DummyPrediction(summary="Summary.")

    result: MetricResult = metric.evaluate(example=example, prediction=prediction)

    # Default score is 1 -> scaled (1-1)/4 = 0.0
    assert result.score == 0.0
    assert "Missing evaluation data" in result.reason
