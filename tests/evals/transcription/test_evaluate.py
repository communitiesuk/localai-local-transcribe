from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml

from evals.transcription.src import evaluate
from evals.transcription.src.constants import PROCESSING_SPEED_DRIFT_THRESHOLDS, SPEAKER_COUNT_DRIFT_THRESHOLDS
from evals.transcription.src.core.dataset import DEFAULT_DATASET_NAME
from evals.transcription.src.evaluate import run_evaluation
from tests.evals.transcription.conftest import FakeAdapter, FakeDataset


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
        patch("evals.transcription.src.evaluate.load_benchmark_dataset", return_value=mock_dataset) as mock_load,
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
            **expected_load_call,
            dataset_name="ami",
            samples_per_group=None,
            input_dir=None,
        )
        mock_run.assert_called_once()
        assert len(mock_run.call_args.kwargs["adapters"]) == 1
        assert mock_run.call_args.kwargs["indices"] == list(range(dataset_len))
        mock_save.assert_called_once()


@pytest.mark.parametrize("input_dir", ["../cache", None])
def test_main_parses_yaml_and_resolves_relative_input_dir(tmp_path, monkeypatch, input_dir):
    config_dir = tmp_path / "nested" / "configs"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "evaluation.yaml"
    config = {
        "num_samples": 2,
        "sample_duration_fraction": 0.25,
        "prepare_only": True,
        "max_workers": 3,
        "check_drift_thresholds": False,
        "adapters": ["azure"],
    }
    if input_dir is not None:
        config["input_dir"] = input_dir
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["evaluate", "--config", str(config_path)])
    with (
        patch.object(evaluate, "run_evaluation", return_value=0) as run,
        pytest.raises(SystemExit) as exit_info,
    ):
        evaluate.main()
    assert exit_info.value.code == 0
    run.assert_called_once_with(
        num_samples=2,
        sample_duration_fraction=0.25,
        prepare_only=True,
        max_workers=3,
        adapter_names=["azure"],
        check_drift_thresholds=False,
        dataset_name=DEFAULT_DATASET_NAME,
        samples_per_group=None,
        input_dir=(config_dir / input_dir).resolve() if input_dir is not None else None,
    )


@pytest.mark.parametrize("prepare_only", [False, True])
@pytest.mark.parametrize("num_samples", [0, 2])
def test_empty_dataset_fails_before_adapter_calls_or_results(tmp_path, monkeypatch, prepare_only, num_samples):
    monkeypatch.setattr(evaluate, "WORKDIR", tmp_path)
    dataset = MagicMock()
    dataset.__len__.return_value = 0
    with (
        patch.object(evaluate, "load_benchmark_dataset", return_value=dataset),
        patch.object(evaluate, "ServiceTranscriptionAdapter") as adapter,
        patch.object(evaluate, "run_engines_parallel") as run,
        patch.object(evaluate, "save_results") as save,
        pytest.raises(ValueError, match="produced no samples"),
    ):
        run_evaluation(num_samples=num_samples, prepare_only=prepare_only, adapter_names=["azure"])
    adapter.assert_not_called()
    run.assert_not_called()
    save.assert_not_called()


@pytest.mark.parametrize("dataset_supports_diarization", [False, True])
def test_runner_and_drift_agree_on_each_engine_capability(tmp_path, monkeypatch, dataset_supports_diarization):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake audio")
    dataset = FakeDataset(
        [
            {"text": "hello world", "audio": {"path": str(audio_path)}}
            for _ in range(SPEAKER_COUNT_DRIFT_THRESHOLDS.n_meetings)
        ]
    )
    dataset.supports_diarization = dataset_supports_diarization
    speakers = FakeAdapter("speakers", "hello world", proc_sec=PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    text_only = FakeAdapter("text_only", "hello world", proc_sec=PROCESSING_SPEED_DRIFT_THRESHOLDS.baseline_ratio)
    text_only.supports_diarization = False
    monkeypatch.setattr(evaluate, "WORKDIR", tmp_path)
    monkeypatch.setattr(evaluate, "load_benchmark_dataset", lambda **_kwargs: dataset)
    monkeypatch.setattr(evaluate, "ADAPTER_REGISTRY", {"speakers": speakers, "text_only": text_only})
    monkeypatch.setattr(evaluate, "ServiceTranscriptionAdapter", lambda service: service)
    monkeypatch.setattr(evaluate, "prepare_audio_for_transcription", lambda sample, _index: sample.audio.path)
    monkeypatch.setattr(evaluate, "get_duration", lambda _path: 1.0)
    assert run_evaluation(adapter_names=["speakers", "text_only"], check_drift_thresholds=True, max_workers=1) == 0
    saved = json.loads(next((tmp_path / "output").glob("evaluation_results_*.json")).read_text())
    review = json.loads(next((tmp_path / "output").glob("drift_review_*.json")).read_text())
    for engine_name, supported in (("speakers", dataset_supports_diarization), ("text_only", False)):
        assert ("wder" in saved["engines"][engine_name][0]["metrics"]) == supported
        verdict = next(
            check
            for check in review["checks"]
            if check["engine_version"] == engine_name and check["metric"] == "corpus_wder"
        )
        assert (verdict["observed"] is not None) == supported
        if not supported:
            assert verdict["outcome"] == "review"
            assert "dataset or adapter" in verdict["detail"]
