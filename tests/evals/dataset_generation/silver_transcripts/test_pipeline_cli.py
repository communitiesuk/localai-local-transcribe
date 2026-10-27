from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evals.dataset_generation.silver_transcripts.src.main import main
from evals.dataset_generation.silver_transcripts.src.pipeline import SilverTranscriptPipeline


def _write_config(config_dir: Path, body: str) -> Path:
    config_dir.mkdir(exist_ok=True)
    config = config_dir / "smoke_test.yaml"
    config.write_text(body, encoding="utf-8")
    return config


def test_smoke_config_runs_generation_with_relative_paths(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    config = _write_config(
        tmp_path / "configs", "input_dir: ../input\nwork_dir: ../smoke_output\nsegment_duration_seconds: null\n"
    )
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])
    monkeypatch.chdir(config.parent)

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 0
    metadata_paths = list((tmp_path / "smoke_output" / "drafts").glob("*/metadata.json"))
    assert len(metadata_paths) == 1
    metadata = json.loads(metadata_paths[0].read_text())
    assert metadata["status"] == "completed"
    assert metadata["segment_duration_seconds"] is None
    assert adapter.calls == 1


def test_main_uses_patched_adapter_for_long_input_without_calling_azure_batch(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../long_output\n")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.soundfile.info",
        lambda _path: SimpleNamespace(frames=7201, samplerate=1),
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 0
    assert adapter.calls == 1
    records = list((tmp_path / "long_output" / "drafts").glob("*/metadata.json"))
    metadata = json.loads(records[0].read_text())
    assert metadata["engine"] == "test_engine"


def test_recorded_generation_failure_exits_non_zero(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    adapter.fail = True
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../failed_output\n")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    metadata_paths = list((tmp_path / "failed_output" / "drafts").glob("*/metadata.json"))
    assert json.loads(metadata_paths[0].read_text())["status"] == "failed"


def test_a_skipped_sample_exits_non_zero(draft_setup, monkeypatch, tmp_path):
    _input_dir, _pipeline, adapter = draft_setup
    config = _write_config(tmp_path / "configs", "input_dir: ../input\nwork_dir: ../legacy_output\n")
    sample_id = SilverTranscriptPipeline._sample_id("sample.wav", "sample")  # noqa: SLF001
    draft_dir = tmp_path / "legacy_output" / "drafts" / sample_id
    draft_dir.mkdir(parents=True)
    (draft_dir / "metadata.json").write_text('{"status": "approved"}', encoding="utf-8")
    monkeypatch.setattr(
        "evals.dataset_generation.silver_transcripts.src.pipeline.ServiceTranscriptionAdapter",
        lambda _service: adapter,
    )
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 1
    assert adapter.calls == 0
    assert json.loads((draft_dir / "metadata.json").read_text()) == {"status": "approved"}


def test_generate_reports_a_missing_config(monkeypatch, tmp_path):
    missing = tmp_path / "configs" / "absent.yaml"
    monkeypatch.setattr("sys.argv", ["main", "--config", str(missing)])

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        main()


def test_generate_requires_an_input_dir_in_the_config(monkeypatch, tmp_path):
    config = tmp_path / "no_input.yaml"
    config.write_text("work_dir: ../output/smoke\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["main", "--config", str(config)])

    with pytest.raises(ValueError, match="input_dir must be specified"):
        main()

