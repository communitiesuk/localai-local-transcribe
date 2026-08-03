from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import dspy
import orjson
import pytest

from evals.summarisation.src.common import AppConfig
from evals.summarisation.src.optimisation.runner import (
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


_LOCAL_ENTRIES = [
    {"speaker": "1", "text": "Hello Mrs Parsons, it's Sandra.", "start_time": 0.0, "end_time": 1.0},
    {
        "speaker": "2",
        "text": "Lovely to hear from you.\nThe tap is still dripping.",
        "start_time": 1.0,
        "end_time": 2.0,
    },
]


def _write_local_dataset(input_dir: Path, *names: str) -> Path:
    input_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (input_dir / f"{name}.json").write_text(
            json.dumps({"theme": "t", "num_speakers": 2, "dialogue_entries": _LOCAL_ENTRIES}),
            encoding="utf-8",
        )
    return input_dir


def _local_cfg(tmp_path: Path, **overrides: object) -> AppConfig:
    return _cfg(
        tmp_path,
        dataset={"name": "final_july_set", "source": "local_dir"},
        **overrides,
    )


def test_load_dspy_devset_local_dir_reads_input_dir(tmp_path):
    _write_local_dataset(tmp_path / "input", "b_call", "a_call")
    cfg = _local_cfg(tmp_path, run={"output_dir": str(tmp_path / "output"), "input_dir": str(tmp_path / "input")})

    devset = load_dspy_devset(cfg, split="test", limit=None)

    assert [ex.example_id for ex in devset] == ["a_call", "b_call"]
    assert devset[0].dialogue_entries == _LOCAL_ENTRIES
    assert set(devset[0].inputs().keys()) == {"dialogue", "dialogue_entries"}


def test_load_dspy_devset_local_dir_applies_limit(tmp_path):
    _write_local_dataset(tmp_path / "input", "a", "b", "c")
    cfg = _local_cfg(tmp_path, run={"output_dir": str(tmp_path / "output"), "input_dir": str(tmp_path / "input")})

    devset = load_dspy_devset(cfg, split="test", limit=2)

    assert len(devset) == 2


def test_load_dspy_devset_local_dir_dataset_path_overrides_input_dir(tmp_path):
    _write_local_dataset(tmp_path / "override", "override_call")
    cfg = _local_cfg(tmp_path, run={"output_dir": str(tmp_path / "output"), "input_dir": str(tmp_path / "input")})

    devset = load_dspy_devset(cfg, split="test", limit=None, dataset_path=tmp_path / "override")

    assert [ex.example_id for ex in devset] == ["override_call"]


def test_load_dspy_devset_local_dir_without_input_dir_raises(tmp_path):
    cfg = _local_cfg(tmp_path)

    with pytest.raises(ValueError, match="run.input_dir must be set"):
        load_dspy_devset(cfg, split="test", limit=None)


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


def test_run_eval_local_dir_summarises_dataset_entries(tmp_path):
    """A local_dir run summarises every transcript in the input dir, entries passed through as-is."""
    _write_local_dataset(tmp_path / "input", "tenancy_call")
    cfg = _local_cfg(
        tmp_path,
        run={"output_dir": str(tmp_path / "output"), "input_dir": str(tmp_path / "input")},
        metrics=["accuracy"],
    )

    mock_generated = Mock()
    mock_generated.text = "Generated summary"
    mock_generated.hallucinations = []
    mock_generated.total_claims = 5

    mock_judge_response = {"dimensions": {"accuracy": {"score": "5", "rationale": "Accurate"}}}

    with (
        patch(
            "evals.summarisation.src.optimisation.runner.generate_summary",
            new_callable=AsyncMock,
            return_value=mock_generated,
        ) as mock_summarise,
        patch(
            "evals.summarisation.src.optimisation.runner.call_llm_judge_parallel",
            new_callable=AsyncMock,
            return_value=mock_judge_response,
        ) as mock_judge,
        patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
        patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
    ):
        mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
        mock_tokenizer.return_value.encode = Mock(return_value=[1])

        _, results_path, summary_path, _ = run_eval(cfg, split="test", limit=None, prompt_version="v1")

    # The generated entries reach the summariser untouched: a multi-line utterance stays one entry.
    assert mock_summarise.await_args.args[0] == _LOCAL_ENTRIES

    summary = orjson.loads(summary_path.read_bytes())
    assert summary["n"] == 1
    assert summary["split"] is None

    record = orjson.loads(results_path.read_text(encoding="utf-8").splitlines()[0])
    assert record["example_id"] == "tenancy_call"
    # The judge sees the dataset's own entries, numbered for citation resolution.
    assert mock_judge.await_args.kwargs["transcript_text"].startswith("[0] ")
    assert "The tap is still dripping." in mock_judge.await_args.kwargs["transcript_text"]
