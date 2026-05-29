from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import dspy
import pytest

from evals.summarisation.src.common import AppConfig, DialogExample
from evals.summarisation.src.optimisation.runner import (
    _dialogue_to_entries,
    _elapsed_ms,
    _load_data_pairs,
    _p50,
    _prepare_run_paths,
    _to_dspy_devset,
    _utc_now,
    call_llm_judge_parallel,
    run_eval,
)

_MINIMAL_PROMPTS = {"judge_template_path": "prompts/judge.jinja2"}
_MINIMAL_DATASET = {
    "name": "test_dataset",
    "dialogue_field": "dialogue",
    "reference_summary_field": "summary",
}


def _cfg(tmp_path: Path | None = None, **overrides: object) -> AppConfig:
    return AppConfig.model_validate(
        {
            "run": {"output_dir": str(tmp_path / "output") if tmp_path else "output"},
            "dataset": _MINIMAL_DATASET,
            "judge": {"pass_threshold": 4},
            "prompts": _MINIMAL_PROMPTS,
            **overrides,
        }
    )


def test_utc_now():
    result = _utc_now()
    assert isinstance(result, datetime)
    assert result.tzinfo == UTC


def test_elapsed_ms():
    assert _elapsed_ms(1.0, 1.5) == 500


def test_elapsed_ms_rounds():
    assert _elapsed_ms(1.0, 1.0006) == 1


def test_p50_empty_list():
    assert _p50([]) == 0


def test_p50_single_value():
    assert _p50([100]) == 100


def test_p50_odd_count():
    assert _p50([10, 20, 30, 40, 50]) == 30


def test_p50_even_count():
    assert _p50([10, 20, 30, 40]) == 30


def test_p50_unsorted_input():
    assert _p50([50, 10, 30, 20, 40]) == 30


def test_prepare_run_paths_creates_directories(tmp_path):
    out_dir, results_path, summary_path, hallucination_inputs_path = _prepare_run_paths(_cfg(tmp_path), "test-run-123")

    assert out_dir.exists()
    assert out_dir == tmp_path / "output" / "test-run-123"
    assert results_path == out_dir / "results.jsonl"
    assert summary_path == out_dir / "summary.json"
    assert hallucination_inputs_path == out_dir / "hallucination_inputs.json"


def test_load_data_pairs_basic():
    mock_dataset = {
        "test": [
            {"id": "1", "dialogue": "Hello world", "summary": "Greeting"},
            {"id": "2", "dialogue": "Goodbye", "summary": "Farewell"},
        ]
    }

    with patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value=mock_dataset):
        examples = _load_data_pairs(_cfg(), split="test", limit=None)

    assert len(examples) == 2
    assert examples[0].example_id == "1"
    assert examples[0].dialogue == "Hello world"
    assert examples[0].reference_summary == "Greeting"


def test_load_data_pairs_with_limit():
    mock_rows = [
        {"id": "1", "dialogue": "First", "summary": "S1"},
        {"id": "2", "dialogue": "Second", "summary": "S2"},
        {"id": "3", "dialogue": "Third", "summary": "S3"},
    ]
    mock_split = Mock()
    mock_split.__iter__ = Mock(return_value=iter(mock_rows))
    mock_split.select = Mock(return_value=mock_rows[:2])
    mock_split.__len__ = Mock(return_value=3)

    with patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}):
        examples = _load_data_pairs(_cfg(), split="test", limit=2)

    mock_split.select.assert_called_once()
    assert len(examples) == 2


def test_load_data_pairs_missing_id_uses_index():
    mock_dataset = {"test": [{"dialogue": "Hello", "summary": "Hi"}]}

    with patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value=mock_dataset):
        examples = _load_data_pairs(_cfg(), split="test", limit=None)

    assert examples[0].example_id == "0"


def test_to_dspy_devset():
    examples = [
        DialogExample(example_id="1", dialogue="Hello", reference_summary="Hi"),
        DialogExample(example_id="2", dialogue="Bye", reference_summary="Goodbye"),
    ]
    devset = _to_dspy_devset(examples)

    assert len(devset) == 2
    assert isinstance(devset[0], dspy.Example)
    assert devset[0].example_id == "1"
    assert devset[0].dialogue == "Hello"
    assert "dialogue" in devset[0].inputs()


def test_dialogue_to_entries_dialogsum_format():
    dialogue = "#Person1#: Hello there.\n#Person2#: How are you?"
    entries = _dialogue_to_entries(dialogue)

    assert len(entries) == 2
    assert entries[0]["speaker"] == "Person1"
    assert entries[0]["text"] == "Hello there."
    assert entries[1]["speaker"] == "Person2"


def test_dialogue_to_entries_plain_lines():
    dialogue = "First line.\nSecond line."
    entries = _dialogue_to_entries(dialogue)

    assert len(entries) == 2
    assert entries[0]["speaker"] == "Speaker"
    assert entries[0]["text"] == "First line."


def test_dialogue_to_entries_skips_blank_lines():
    dialogue = "#A#: Hello.\n\n#B#: Hi."
    entries = _dialogue_to_entries(dialogue)
    assert len(entries) == 2


def test_dialogue_to_entries_has_timestamps():
    dialogue = "#A#: Hello.\n#B#: Hi."
    entries = _dialogue_to_entries(dialogue)
    assert entries[0]["start_time"] == 0.0
    assert entries[0]["end_time"] == 1.0
    assert entries[1]["start_time"] == 1.0
    assert entries[1]["end_time"] == 2.0


def test_run_eval_contract_returns_valid_paths(tmp_path):
    """CONTRACT TEST: run_eval returns valid run_id and Path objects for results."""
    cfg = _cfg(tmp_path, metrics=["faithfulness"])

    mock_rows = [{"id": "1", "dialogue": "#A#: Hello.", "summary": "Greeting"}]
    mock_split = Mock()
    mock_split.__iter__ = Mock(return_value=iter(mock_rows))
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    mock_evaluator = MagicMock()
    mock_evaluator.return_value = 0.95

    mock_rubric = {"dimensions": {"accuracy": {"score": 5, "rationale": "excellent"}}}

    with (
        patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
        patch(
            "evals.summarisation.src.optimisation.runner.generate_summary",
            new_callable=AsyncMock,
            return_value=("Generated summary [1]", 5, []),
        ),
        patch(
            "evals.summarisation.src.optimisation.runner.call_llm_judge_parallel",
            new_callable=AsyncMock,
            return_value=mock_rubric,
        ),
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.Evaluate", return_value=mock_evaluator),
    ):
        mock_settings.return_value.BEST_LLM_MODEL_NAME = "test-model"
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-fast-model"

        run_id, results_path, summary_path, hallucination_inputs_path = run_eval(
            cfg,
            split="test",
            limit=1,
            prompt_version="v1",
        )

    assert run_id is not None
    assert isinstance(results_path, Path)
    assert isinstance(summary_path, Path)
    assert isinstance(hallucination_inputs_path, Path)
    assert hallucination_inputs_path.name == "hallucination_inputs.json"
    mock_evaluator.assert_called_once()


@pytest.mark.asyncio
async def test_call_llm_judge_parallel():
    from unittest.mock import AsyncMock, patch

    mock_response = {"dimensions": {"accuracy": {"score": 5, "rationale": "excellent"}}}

    # Patch the actual implementation location, not an intermediate module
    with patch(
        "evals.summarisation.src.optimisation.runner.call_llm_judge_parallel",  # Changed path
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_call:
        result = await call_llm_judge_parallel(
            summary_id="id",
            transcript_ref="ref",
            transcript_text="dialogue",
            summary_text="summary",
            dimensions=["accuracy"],
        )

    assert result == {"dimensions": {"accuracy": {"score": 5, "rationale": "excellent"}}}
    mock_call.assert_called_once()