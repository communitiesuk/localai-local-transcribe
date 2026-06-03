from __future__ import annotations

from unittest.mock import MagicMock, patch

import dspy

from evals.summarisation.src.common import DialogExample
from evals.summarisation.src.common.metric import (
    DialogSummaryMetric,
    load_system_prompt,
    make_dynamic_signature,
)


def test_load_system_prompt_exists():
    """Test that load_system_prompt loads and renders the system prompt with rubric."""
    # faithfulness maps to accuracy
    prompt_text = load_system_prompt("faithfulness")
    assert "You are an expert AI quality assurance judge" in prompt_text
    assert "Dimension: Factual Accuracy" in prompt_text


def test_load_system_prompt_fallback():
    """Test that load_system_prompt falls back gracefully when rubric does not exist."""
    prompt_text = load_system_prompt("nonexistent_metric")
    assert "You are an expert AI quality assurance judge" in prompt_text
    assert "Rate the candidate summary for the criterion: nonexistent_metric" in prompt_text


def test_make_dynamic_signature():
    """Test that make_dynamic_signature creates a valid DSPy signature subclass."""
    sig = make_dynamic_signature("test_metric", "Test Rubric content")
    assert issubclass(sig, dspy.Signature)
    assert "dialogue" in sig.model_fields
    assert "reference_summary" in sig.model_fields
    assert "candidate_summary" in sig.model_fields
    assert "evaluation_result" in sig.model_fields
    assert "Test Rubric content" in sig.__doc__


def test_dialog_summary_metric_evaluate_success():
    """Test evaluate method with a successful JSON response from the model."""
    mock_lm = MagicMock(spec=dspy.LM)
    metric = DialogSummaryMetric(
        name="judge_faithfulness",
        criterion="faithfulness",
        pass_threshold=4,
        lm=mock_lm,
    )

    example = DialogExample(
        example_id="1",
        dialogue="Hello world",
        reference_summary="Greeting",
    )
    prediction = dspy.Prediction(summary="Hello world")

    # Mock prediction output
    mock_pred = MagicMock()
    mock_pred.evaluation_result = '{"rating": 5, "reason": "Perfect match"}'

    with patch("evals.summarisation.src.common.metric.dspy.Predict") as mock_predict_class:
        mock_predict_instance = MagicMock()
        mock_predict_instance.return_value = mock_pred
        mock_predict_class.return_value = mock_predict_instance

        res = metric.evaluate(example=example, prediction=prediction)

        assert res.score == 1.0
        assert "rating=5" in res.reason
        assert "Perfect match" in res.reason


def test_dialog_summary_metric_evaluate_below_threshold():
    """Test evaluate method when rating is below the pass threshold."""
    mock_lm = MagicMock(spec=dspy.LM)
    metric = DialogSummaryMetric(
        name="judge_faithfulness",
        criterion="faithfulness",
        pass_threshold=4,
        lm=mock_lm,
    )

    example = DialogExample(
        example_id="1",
        dialogue="Hello world",
        reference_summary="Greeting",
    )
    prediction = dspy.Prediction(summary="Hello world")

    # Mock prediction output
    mock_pred = MagicMock()
    mock_pred.evaluation_result = '{"rating": 3, "reason": "Slight hallucination"}'

    with patch("evals.summarisation.src.common.metric.dspy.Predict") as mock_predict_class:
        mock_predict_instance = MagicMock()
        mock_predict_instance.return_value = mock_pred
        mock_predict_class.return_value = mock_predict_instance

        res = metric.evaluate(example=example, prediction=prediction)

        assert res.score == 0.0
        assert "rating=3" in res.reason
        assert "Slight hallucination" in res.reason


def test_dialog_summary_metric_evaluate_invalid_json():
    """Test evaluate method when the LLM returns invalid JSON."""
    mock_lm = MagicMock(spec=dspy.LM)
    metric = DialogSummaryMetric(
        name="judge_faithfulness",
        criterion="faithfulness",
        pass_threshold=4,
        lm=mock_lm,
    )

    example = DialogExample(
        example_id="1",
        dialogue="Hello world",
        reference_summary="Greeting",
    )
    prediction = dspy.Prediction(summary="Hello world")

    # Mock prediction output with bad JSON
    mock_pred = MagicMock()
    mock_pred.evaluation_result = "This is not JSON at all."

    with patch("evals.summarisation.src.common.metric.dspy.Predict") as mock_predict_class:
        mock_predict_instance = MagicMock()
        mock_predict_instance.return_value = mock_pred
        mock_predict_class.return_value = mock_predict_instance

        res = metric.evaluate(example=example, prediction=prediction)

        assert res.score == 0.0  # Fails due to default rating of 1
        assert "rating=1" in res.reason
        assert "No JSON object found in output" in res.reason
