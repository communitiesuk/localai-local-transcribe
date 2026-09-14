from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from evals.transcription.src.evaluate import (
    EvaluationRunOutcome,
    _run_blob_evaluation,
    _run_from_config,
    run_evaluation,
    run_evaluation_with_outputs,
)
from evals.transcription.src.models import EvaluationConfig


@pytest.mark.parametrize(
    ("kwargs", "dataset_len", "expected_load_call"),
    [
        (
            {"num_samples": 5, "adapter_names": ["azure"]},
            10,
            {"num_samples": 5, "sample_duration_fraction": None},
        ),
        (
            {"sample_duration_fraction": 0.5, "adapter_names": ["azure"]},
            10,
            {"num_samples": None, "sample_duration_fraction": 0.5},
        ),
        (
            {"adapter_names": ["azure"]},
            2,
            {"num_samples": None, "sample_duration_fraction": None},
        ),
    ],
)
def test_run_evaluation(tmp_path, monkeypatch, kwargs, dataset_len, expected_load_call):
    monkeypatch.setattr("evals.transcription.src.evaluate.WORKDIR", tmp_path)

    mock_dataset = MagicMock()
    mock_dataset.__len__ = MagicMock(return_value=dataset_len)
    mock_dataset.__getitem__ = MagicMock(return_value=MagicMock(text="test", audio=MagicMock(path="/fake/path.wav")))
    mock_dataset.dataset_version = "test_v1"
    mock_dataset.dataset_split = "test"

    with (
        patch("evals.transcription.src.evaluate._load_dataset", return_value=mock_dataset) as mock_load,
        patch("evals.transcription.src.evaluate.run_engines_parallel", return_value=[]) as mock_run,
        patch("evals.transcription.src.evaluate.save_results") as mock_save,
        patch(
            "evals.transcription.src.evaluate.prepare_audio_for_transcription",
            return_value="/fake/prepared.wav",
        ),
        patch("evals.transcription.src.evaluate.get_duration", return_value=1.0),
    ):
        result = run_evaluation(**kwargs)

        assert result == 0
        mock_load.assert_called_once_with(
            "ami",
            None,
            expected_load_call["num_samples"],
            expected_load_call["sample_duration_fraction"],
        )
        mock_run.assert_called_once()
        assert len(mock_run.call_args.kwargs["adapters"]) == 1
        assert mock_run.call_args.kwargs["indices"] == list(range(dataset_len))
        mock_save.assert_called_once()


def test_run_evaluation_requires_at_least_one_adapter(tmp_path, monkeypatch):
    monkeypatch.setattr("evals.transcription.src.evaluate.WORKDIR", tmp_path)

    mock_dataset = MagicMock()
    mock_dataset.__len__ = MagicMock(return_value=1)
    mock_dataset.dataset_version = "test_v1"
    mock_dataset.dataset_split = "test"

    with (
        patch("evals.transcription.src.evaluate._load_dataset", return_value=mock_dataset),
        pytest.raises(ValueError, match="adapter_names is required"),
    ):
        run_evaluation_with_outputs(adapter_names=[])


def test_evaluation_config_requires_adapters_unless_prepare_only():
    with pytest.raises(ValidationError, match="adapters must contain at least one adapter"):
        EvaluationConfig.model_validate({"prepare_only": False})

    config = EvaluationConfig.model_validate({"prepare_only": True})

    assert config.adapters == []


def test_evaluation_config_rejects_prepare_only_with_blob():
    with pytest.raises(ValidationError, match="prepare_only is for local dataset setup only"):
        EvaluationConfig.model_validate(
            {
                "prepare_only": True,
                "blob": {
                    "enabled": True,
                    "input_prefix": "transcription/smoke-test/audio",
                },
            }
        )


def test_run_from_config_uses_configured_dataset_loader(tmp_path):
    config = EvaluationConfig.model_validate(
        {
            "dataset_loader": "audio_files",
            "adapters": ["azure"],
        }
    )
    mock_dataset = MagicMock()
    mock_dataset.__len__ = MagicMock(return_value=1)
    mock_dataset.dataset_version = "test_v1"
    mock_dataset.dataset_split = "test"

    with (
        patch("evals.transcription.src.evaluate._load_dataset", return_value=mock_dataset) as mock_load,
        patch("evals.transcription.src.evaluate.run_engines_parallel", return_value=[]),
        patch("evals.transcription.src.evaluate.save_results"),
        patch("evals.transcription.src.evaluate.save_summary_results"),
        patch("evals.transcription.src.evaluate.prepare_audio_for_transcription"),
        patch("evals.transcription.src.evaluate.get_duration", return_value=1.0),
    ):
        _run_from_config(config, output_dir=tmp_path)

    mock_load.assert_called_once_with("audio_files", None, None, None)


def test_run_ids_are_unique_within_same_second(tmp_path, monkeypatch):
    monkeypatch.setattr("evals.transcription.src.evaluate.WORKDIR", tmp_path)

    mock_dataset = MagicMock()
    mock_dataset.__len__ = MagicMock(return_value=1)
    mock_dataset.dataset_version = "test_v1"
    mock_dataset.dataset_split = "test"

    with (
        patch("evals.transcription.src.evaluate._load_dataset", return_value=mock_dataset),
        patch("evals.transcription.src.evaluate.run_engines_parallel", return_value=[]),
        patch("evals.transcription.src.evaluate.save_results"),
        patch("evals.transcription.src.evaluate.save_summary_results"),
        patch("evals.transcription.src.evaluate.prepare_audio_for_transcription"),
        patch("evals.transcription.src.evaluate.get_duration", return_value=1.0),
    ):
        first = run_evaluation_with_outputs(adapter_names=["azure"])
        second = run_evaluation_with_outputs(adapter_names=["azure"])

    assert first.run_id != second.run_id


def test_blob_evaluation_stages_transcription_prefix_and_publishes_split_outputs(tmp_path):
    config = EvaluationConfig.model_validate(
        {
            "num_samples": 1,
            "dataset_loader": "audio_files",
            "max_workers": 1,
            "prepare_only": False,
            "adapters": ["azure"],
            "blob": {
                "enabled": True,
                "input_prefix": "transcription/smoke-test/audio",
                "output_prefix": "",
                "restricted_account_url": "https://restricted.blob.core.windows.net",
                "shared_account_url": "https://shared.blob.core.windows.net",
            },
        }
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")
    (run_dir / "results.json").write_text('{"engines": {}}', encoding="utf-8")
    (run_dir / "words.json").write_text("[]", encoding="utf-8")
    outcome = EvaluationRunOutcome(
        exit_code=0,
        run_id="eval_run1",
        run_output_dir=run_dir,
        detailed_results_path=run_dir / "results.json",
        summary_path=run_dir / "summary.json",
    )
    artifact_dir = tmp_path / "artifact"
    fake_blob = MagicMock()

    with (
        patch("evals.transcription.src.evaluate.EvalBlobStorage.from_account_urls", return_value=fake_blob),
        patch(
            "evals.transcription.src.evaluate.stage_dataset_prefix",
            return_value=tmp_path / "input",
        ) as stage,
        patch("evals.transcription.src.evaluate._load_dataset", return_value=MagicMock()) as load_dataset,
        patch("evals.transcription.src.evaluate._run_from_config", return_value=outcome) as run_from_config,
    ):
        exit_code = _run_blob_evaluation(config, artifact_dir)

    assert exit_code == 0
    stage.assert_called_once()
    assert stage.call_args.args[1] == "transcription/smoke-test/audio"
    load_dataset.assert_called_once_with("audio_files", tmp_path / "input", 1, None)
    run_from_config.assert_called_once()

    dests = {call.args[0]: call.args[1] for call in fake_blob.upload_file.call_args_list}
    assert dests["output"] == "transcription/eval_run1/summary.json"
    debug_blobs = {call.args[1] for call in fake_blob.upload_file.call_args_list if call.args[0] == "debug"}
    assert "transcription/eval_run1/results.json" in debug_blobs
    assert "transcription/eval_run1/words.json" in debug_blobs
    assert (artifact_dir / "transcription" / "eval_run1" / "summary.json").read_text(encoding="utf-8") == "{}"
