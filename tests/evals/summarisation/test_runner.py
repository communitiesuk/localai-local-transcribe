from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import dspy

from evals.summarisation.src.common import AppConfig, run_halted
from evals.summarisation.src.optimisation.runner import (
    _build_run_summary,
    _dialogue_to_entries,
    _elapsed_ms,
    _p50,
    _utc_now,
    load_dspy_devset,
    prepare_run_paths,
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
    results_path, summary_path, hallucination_inputs_path = prepare_run_paths(
        _cfg(tmp_path).run.output_dir, "test-run-123"
    )

    assert results_path.parent.exists()
    assert results_path == tmp_path / "output" / "test-run-123" / "results.jsonl"
    assert summary_path == tmp_path / "output" / "test-run-123" / "summary.json"
    assert hallucination_inputs_path == tmp_path / "output" / "test-run-123" / "hallucination_inputs.json"


def test_load_dspy_devset_basic():
    mock_dataset = {
        "test": [
            {"id": "1", "dialogue": "Hello world", "summary": "Greeting"},
            {"id": "2", "dialogue": "Goodbye", "summary": "Farewell"},
        ]
    }

    with patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value=mock_dataset):
        devset = load_dspy_devset(_cfg(), split="test", limit=None)

    assert len(devset) == 2
    assert isinstance(devset[0], dspy.Example)
    assert devset[0].example_id == "1"
    assert devset[0].dialogue == "Hello world"
    assert devset[0].reference_summary == "Greeting"
    assert "dialogue" in devset[0].inputs()


def test_load_dspy_devset_with_limit():
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
        devset = load_dspy_devset(_cfg(), split="test", limit=2)

    mock_split.select.assert_called_once()
    assert len(devset) == 2


def test_load_dspy_devset_missing_id_uses_index():
    mock_dataset = {"test": [{"dialogue": "Hello", "summary": "Hi"}]}

    with patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value=mock_dataset):
        devset = load_dspy_devset(_cfg(), split="test", limit=None)

    assert devset[0].example_id == "0"


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


def test_run_halted_detects_evaluate_stage_error():
    assert run_halted({"errors": [{"stage": "evaluate", "error": "halted before completion: ..."}]})


def test_run_halted_ignores_per_example_errors():
    # A completed run with a transient judge failure is not a halt.
    assert not run_halted({"errors": [{"stage": "judge", "example_id": "x", "error": "boom"}]})


def test_run_halted_handles_missing_errors_key():
    assert not run_halted({})


def test_run_eval_contract_returns_valid_paths(tmp_path):
    """CONTRACT TEST: run_eval returns valid run_id and Path objects for results."""
    cfg = _cfg(tmp_path, metrics=["accuracy"])

    mock_rows = [{"id": "1", "dialogue": "#A#: Hello.", "summary": "Greeting"}]
    mock_split = Mock()
    mock_split.__iter__ = Mock(return_value=iter(mock_rows))
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    mock_generated = Mock()
    mock_generated.text = "Generated summary"
    mock_generated.hallucinations = []
    mock_generated.total_claims = 5

    mock_judge_response = {
        "dimensions": {
            "readability": {"score": "5", "rationale": "Good"},
            "accuracy": {"score": "5", "rationale": "Accurate"},
        }
    }

    with (
        patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
        patch(
            "evals.summarisation.src.optimisation.runner.generate_summary",
            new_callable=AsyncMock,
            return_value=mock_generated,
        ),
        patch(
            "evals.summarisation.src.optimisation.runner.call_llm_judge_parallel",
            new_callable=AsyncMock,
            return_value=mock_judge_response,
        ),
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
    ):
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
        mock_tokenizer.return_value.encode = Mock(return_value=[1, 2, 3, 4, 5])

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


def test_build_run_summary_records_errors():
    errors = [{"stage": "judge", "example_id": "x1", "error": "RuntimeError: boom"}]
    summary = _build_run_summary(
        run_id="r1",
        split="test",
        devset=[],
        metrics_summary={},
        summarize_ms_values=[],
        judge_ms_values=[],
        errors=errors,
    )
    assert summary["errors"] == errors


def test_build_run_summary_defaults_errors_to_empty():
    summary = _build_run_summary(
        run_id="r1",
        split="test",
        devset=[],
        metrics_summary={},
        summarize_ms_values=[],
        judge_ms_values=[],
    )
    assert summary["errors"] == []


def test_run_eval_survives_dspy_halt_and_records_it(tmp_path):
    """When dspy halts past its error budget, run_eval finalizes and returns instead of raising."""
    cfg = _cfg(tmp_path, metrics=["accuracy"])

    mock_rows = [{"id": "1", "dialogue": "#A#: Hello.", "summary": "Greeting"}]
    mock_split = Mock()
    mock_split.__iter__ = Mock(return_value=iter(mock_rows))
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    # dspy's Evaluate(...) returns an evaluator; calling it raises once max_errors is exceeded.
    halting_evaluator = Mock(side_effect=RuntimeError("Execution cancelled due to errors or interruption."))

    with (
        patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
        patch("evals.summarisation.src.optimisation.runner.Evaluate", return_value=halting_evaluator),
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
    ):
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
        mock_tokenizer.return_value.encode = Mock(return_value=[1])

        # Must not raise: a halted run still returns its finalized paths.
        run_id, results_path, summary_path, hallucination_inputs_path = run_eval(
            cfg, split="test", limit=1, prompt_version="v1"
        )

    assert run_id
    assert summary_path.exists(), "summary.json should be written even when the eval halts"
    summary = json.loads(summary_path.read_text())
    assert any(e["stage"] == "evaluate" for e in summary["errors"]), "the halt should be recorded"


def test_run_eval_records_ai_call_failures_in_summary(tmp_path):
    """When an AI call (here the judge) fails, summary.json records the error."""
    cfg = _cfg(tmp_path, metrics=["accuracy"])

    mock_rows = [{"id": "1", "dialogue": "#A#: Hello.", "summary": "Greeting"}]
    mock_split = Mock()
    mock_split.__iter__ = Mock(return_value=iter(mock_rows))
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    mock_generated = Mock()
    mock_generated.text = "Generated summary"
    mock_generated.hallucinations = []
    mock_generated.total_claims = 5

    with (
        patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
        patch(
            "evals.summarisation.src.optimisation.runner.generate_summary",
            new_callable=AsyncMock,
            return_value=mock_generated,
        ),
        patch(
            "evals.summarisation.src.optimisation.runner.call_llm_judge_parallel",
            new_callable=AsyncMock,
            side_effect=RuntimeError("judge exploded"),
        ),
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
    ):
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
        mock_tokenizer.return_value.encode = Mock(return_value=[1, 2, 3, 4, 5])

        # dspy may re-raise after hitting its error budget; summary is still written in the
        # runner's finally block, which is what we assert on.
        with contextlib.suppress(Exception):
            run_eval(cfg, split="test", limit=1, prompt_version="v1")

    summary_files = list((tmp_path / "output").rglob("summary.json"))
    assert summary_files, "summary.json should be written even when AI calls fail"
    summary = json.loads(summary_files[0].read_text())
    assert summary["errors"], "AI-call errors should be recorded in the summary"
    assert summary["errors"][0]["stage"] == "judge"
    assert "judge exploded" in summary["errors"][0]["error"]


def test_run_eval_records_malformed_judge_payload_in_summary(tmp_path):
    """A 200 response with a malformed judge payload is captured with an example_id, not opaque."""
    cfg = _cfg(tmp_path, metrics=["accuracy"])

    mock_rows = [{"id": "1", "dialogue": "#A#: Hello.", "summary": "Greeting"}]
    mock_split = Mock()
    mock_split.__iter__ = Mock(return_value=iter(mock_rows))
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    mock_generated = Mock()
    mock_generated.text = "Generated summary"
    mock_generated.hallucinations = []
    mock_generated.total_claims = 5

    # 200 OK but truncated: the "score" key is missing, so metric extraction raises KeyError.
    malformed_judge_response = {"dimensions": {"accuracy": {"rationale": "no score field"}}}

    with (
        patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
        patch(
            "evals.summarisation.src.optimisation.runner.generate_summary",
            new_callable=AsyncMock,
            return_value=mock_generated,
        ),
        patch(
            "evals.summarisation.src.optimisation.runner.call_llm_judge_parallel",
            new_callable=AsyncMock,
            return_value=malformed_judge_response,
        ),
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
    ):
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
        mock_tokenizer.return_value.encode = Mock(return_value=[1, 2, 3, 4, 5])

        with contextlib.suppress(Exception):
            run_eval(cfg, split="test", limit=1, prompt_version="v1")

    summary_files = list((tmp_path / "output").rglob("summary.json"))
    assert summary_files, "summary.json should be written even when the judge payload is malformed"
    summary = json.loads(summary_files[0].read_text())
    assert summary["errors"], "malformed judge payloads should be recorded, not silently dropped"
    assert summary["errors"][0]["stage"] == "judge"
    assert summary["errors"][0]["example_id"] == "1"
