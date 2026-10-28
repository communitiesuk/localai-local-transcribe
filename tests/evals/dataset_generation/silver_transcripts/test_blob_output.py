from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from evals.dataset_generation.silver_transcripts.src.blob_output import main, publish_silver_outputs


def test_publishes_all_draft_files_to_restricted_debug_container(tmp_path: Path) -> None:
    draft = tmp_path / "drafts" / "meeting"
    segment = draft / "segments" / "segment_0000"
    segment.mkdir(parents=True)
    (draft / "draft.txt").write_text("transcript")
    (draft / "summary.json").write_text("{}")
    (segment / "audio.mp3").write_bytes(b"audio")
    blob = MagicMock()

    with patch(
        "evals.dataset_generation.silver_transcripts.src.blob_output.EvalBlobStorage.from_account_urls",
        return_value=blob,
    ) as factory:
        published = publish_silver_outputs(tmp_path, "123")

    factory.assert_called_once_with(require_shared=False)
    assert set(published.values()) == {
        "debug/silver-transcripts/123/drafts/meeting/draft.txt",
        "debug/silver-transcripts/123/drafts/meeting/summary.json",
        "debug/silver-transcripts/123/drafts/meeting/segments/segment_0000/audio.mp3",
    }
    assert {call.args[0] for call in blob.upload_file.call_args_list} == {"debug"}


def test_missing_output_directory_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        publish_silver_outputs(tmp_path / "missing", "123")


def test_upload_failure_propagates(tmp_path: Path) -> None:
    (tmp_path / "draft.txt").write_text("transcript")
    blob = MagicMock()
    blob.upload_file.side_effect = RuntimeError("upload failed")
    with (
        patch(
            "evals.dataset_generation.silver_transcripts.src.blob_output.EvalBlobStorage.from_account_urls",
            return_value=blob,
        ),
        pytest.raises(RuntimeError, match="upload failed"),
    ):
        publish_silver_outputs(tmp_path, "123")


def test_cli_passes_output_directory_and_run_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["blob_output", "--output-dir", str(tmp_path), "--run-id", "123"])
    with patch("evals.dataset_generation.silver_transcripts.src.blob_output.publish_silver_outputs") as publish:
        main()
    publish.assert_called_once_with(tmp_path, "123")


def test_pipeline_publishes_partial_outputs_after_generation_failure() -> None:
    pipeline_path = Path(__file__).resolve().parents[4] / ".azuredevops/pipelines/evals-silver-transcripts.yml"
    pipeline = yaml.safe_load(pipeline_path.read_text(encoding="utf-8"))
    generation, upload = [step for step in pipeline["steps"] if step.get("task") == "AzureCLI@2"]

    assert "##vso[task.setvariable variable=silverOutputReady]true" in generation["inputs"]["inlineScript"]
    assert upload["condition"] == "and(succeededOrFailed(), eq(variables['silverOutputReady'], 'true'))"
    assert "evals.dataset_generation.silver_transcripts.src.blob_output" in upload["inputs"]["inlineScript"]
    assert "$(Build.BuildId)" in upload["inputs"]["inlineScript"]
