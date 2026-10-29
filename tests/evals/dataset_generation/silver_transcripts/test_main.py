from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from evals.dataset_generation.silver_transcripts.src.config import SilverTranscriptConfig
from evals.dataset_generation.silver_transcripts.src.main import _run_blob_pipeline, main

RUN_ID_PATTERN = re.compile(r"^silver_\d{8}_\d{6}_[0-9a-f]{8}$")


def _blob_config(**overrides: object) -> SilverTranscriptConfig:
    blob = {"enabled": True, "input_prefix": "transcription/smoke-test/audio", **overrides}
    return SilverTranscriptConfig.model_validate({"blob": blob})


def test_blob_pipeline_stages_generates_and_publishes() -> None:
    config = _blob_config()
    blob = MagicMock()
    staged_input_dirs: list[Path] = []

    def fake_stage(_blob: object, _prefix: str, dest_dir: Path) -> Path:
        staged_input_dirs.append(dest_dir)
        return dest_dir

    def fake_run_pipeline(*, input_dir: Path, work_dir: Path, cutoff_seconds: float) -> int:
        assert input_dir == staged_input_dirs[0]
        assert cutoff_seconds == config.cutoff_seconds
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "draft.txt").write_text("transcript")
        return 0

    draft_existed_at_publish_time = False

    def fake_publish(_blob: object, work_dir: Path, _run_id: str, **_kwargs: object) -> dict[str, str]:
        nonlocal draft_existed_at_publish_time
        draft_existed_at_publish_time = (work_dir / "draft.txt").exists()
        return {}

    with (
        patch(
            "evals.dataset_generation.silver_transcripts.src.main.EvalBlobStorage.from_account_urls",
            return_value=blob,
        ) as factory,
        patch(
            "evals.dataset_generation.silver_transcripts.src.main.stage_dataset_prefix", side_effect=fake_stage
        ) as stage,
        patch("evals.dataset_generation.silver_transcripts.src.main.run_pipeline", side_effect=fake_run_pipeline),
        patch(
            "evals.dataset_generation.silver_transcripts.src.main.publish_run_outputs", side_effect=fake_publish
        ) as publish,
    ):
        exit_code = _run_blob_pipeline(config)

    assert exit_code == 0
    factory.assert_called_once_with(restricted_account_url=None, shared_account_url=None, require_shared=False)
    stage.assert_called_once_with(blob, "transcription/smoke-test/audio", staged_input_dirs[0])
    publish.assert_called_once()
    published_blob, _work_dir, run_id = publish.call_args.args
    assert published_blob is blob
    assert draft_existed_at_publish_time
    assert RUN_ID_PATTERN.match(run_id)
    assert publish.call_args.kwargs == {
        "output_prefix": "",
        "eval_type": "silver-transcripts",
        "results_relative_paths": (),
    }


def test_blob_pipeline_publishes_even_when_generation_reports_failed_samples() -> None:
    config = _blob_config()

    def fake_run_pipeline(*, input_dir: Path, work_dir: Path, cutoff_seconds: float) -> int:  # noqa: ARG001
        work_dir.mkdir(parents=True, exist_ok=True)
        return 1

    with (
        patch("evals.dataset_generation.silver_transcripts.src.main.EvalBlobStorage.from_account_urls"),
        patch(
            "evals.dataset_generation.silver_transcripts.src.main.stage_dataset_prefix",
            side_effect=lambda _blob, _prefix, dest_dir: dest_dir,
        ),
        patch("evals.dataset_generation.silver_transcripts.src.main.run_pipeline", side_effect=fake_run_pipeline),
        patch("evals.dataset_generation.silver_transcripts.src.main.publish_run_outputs", return_value={}) as publish,
    ):
        exit_code = _run_blob_pipeline(config)

    assert exit_code == 1
    publish.assert_called_once()


def test_blob_pipeline_skips_publish_when_work_dir_was_never_created() -> None:
    config = _blob_config()

    def fake_run_pipeline(**_kwargs: object) -> int:
        msg = "input_dir must be specified in the config to generate drafts"
        raise ValueError(msg)

    with (
        patch("evals.dataset_generation.silver_transcripts.src.main.EvalBlobStorage.from_account_urls"),
        patch(
            "evals.dataset_generation.silver_transcripts.src.main.stage_dataset_prefix",
            side_effect=lambda _blob, _prefix, dest_dir: dest_dir,
        ),
        patch("evals.dataset_generation.silver_transcripts.src.main.run_pipeline", side_effect=fake_run_pipeline),
        patch("evals.dataset_generation.silver_transcripts.src.main.publish_run_outputs") as publish,
        pytest.raises(ValueError, match="input_dir must be specified"),
    ):
        _run_blob_pipeline(config)

    publish.assert_not_called()


def test_main_dispatches_to_blob_pipeline_when_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"blob": {"enabled": True, "input_prefix": "transcription/smoke-test/audio"}})
    )
    monkeypatch.setattr(sys, "argv", ["main", "--config", str(config_path)])

    with (
        patch(
            "evals.dataset_generation.silver_transcripts.src.main._run_blob_pipeline", return_value=0
        ) as blob_pipeline,
        patch("evals.dataset_generation.silver_transcripts.src.main.run_pipeline") as local_pipeline,
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 0
    blob_pipeline.assert_called_once()
    local_pipeline.assert_not_called()


def test_pipeline_generates_and_publishes_in_a_single_task() -> None:
    pipeline_path = Path(__file__).resolve().parents[4] / ".azuredevops/pipelines/evals-silver-transcripts.yml"
    pipeline = yaml.safe_load(pipeline_path.read_text(encoding="utf-8"))
    job = pipeline["jobs"][0]
    azure_cli_tasks = [step for step in job["steps"] if step.get("task") == "AzureCLI@2"]

    assert job["pool"]["name"] == "ado-vmss-latest"
    assert job["timeoutInMinutes"] == 360
    assert len(azure_cli_tasks) == 1
    (generation,) = azure_cli_tasks
    assert generation["env"]["AZURE_APIM_AUTH_METHOD"] == "client_secret"
    assert "STORAGE_SERVICE_NAME" not in generation["env"]
    assert "evals.dataset_generation.silver_transcripts.src.main" in generation["inputs"]["inlineScript"]
    assert "blob_input" not in generation["inputs"]["inlineScript"]
    assert "blob_output" not in generation["inputs"]["inlineScript"]
    assert not any(
        step.get("task", "").startswith(("PublishPipelineArtifact@", "PublishBuildArtifacts@")) for step in job["steps"]
    )
