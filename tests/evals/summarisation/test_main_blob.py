"""The main CLI stages inputs from and publishes outputs to blob storage when blob.enabled.

Exercises: evals.summarisation.src.main.app (standard eval, blob publish path).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import yaml
from typer.testing import CliRunner

from evals.summarisation.src.main import app

runner = CliRunner()


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "run": {
            "eval_type": "standard",
            "output_dir": str(tmp_path / "local-out"),
            "limit": 1,
            "prompt_version": "dev",
        },
        "dataset": {
            "name": "synthetic",
            "source": "blob",
            "blob_path": "summarisation/standard/d.jsonl",
            "dialogue_field": "dialogue",
            "reference_summary_field": "summary",
        },
        "judge": {"pass_threshold": 4},
        "metrics": ["accuracy"],
        "prompts": {"judge_template_path": "evals/summarisation/prompts/judge.j2"},
        "blob": {
            "enabled": True,
            "restricted_account_url": "https://restricted.blob.core.windows.net",
            "shared_account_url": "https://shared.blob.core.windows.net",
        },
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def _make_fake_run_eval(
    summary: dict[str, Any],
    threshold_review: dict[str, Any] | None = None,
) -> Callable[..., tuple[str, Path, Path, Path]]:
    def _fake_run_eval(
        cfg: Any,  # noqa: ARG001
        *,
        split: str,  # noqa: ARG001
        limit: int | None,  # noqa: ARG001
        prompt_version: str,  # noqa: ARG001
        output_dir: str | Path,
        dataset_path: Path | None,  # noqa: ARG001
    ) -> tuple[str, Path, Path, Path]:
        run_id = "run1"
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "results.jsonl").write_text("{}\n", encoding="utf-8")
        (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (run_dir / "hallucination_inputs.json").write_text("[]", encoding="utf-8")
        review = threshold_review if threshold_review is not None else {"overall_passed": True}
        (run_dir / "threshold_review.json").write_text(json.dumps(review), encoding="utf-8")
        return run_id, run_dir / "results.jsonl", run_dir / "summary.json", run_dir / "hallucination_inputs.json"

    return _fake_run_eval


_fake_run_eval = _make_fake_run_eval({})


def test_blob_source_without_blob_enabled_is_rejected(tmp_path: Path) -> None:
    cfg = {
        "run": {"eval_type": "standard", "output_dir": str(tmp_path / "out")},
        "dataset": {"name": "synthetic", "source": "blob", "blob_path": "summarisation/standard/d.jsonl"},
        "judge": {"pass_threshold": 4},
        "prompts": {"judge_template_path": "evals/summarisation/prompts/judge.j2"},
        "blob": {"enabled": False},
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    result = runner.invoke(app, ["--config", str(path)])

    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert "blob.enabled" in str(result.exception)


def test_standard_eval_publishes_split_outputs(tmp_path: Path) -> None:
    config = _write_config(tmp_path)
    fake_blob = MagicMock()

    with (
        patch("evals.summarisation.src.main.EvalBlobStorage.from_account_urls", return_value=fake_blob) as make_blob,
        patch("evals.summarisation.src.optimisation.run_eval", side_effect=_fake_run_eval),
    ):
        result = runner.invoke(app, ["--config", str(config)])

    assert result.exit_code == 0, result.output
    make_blob.assert_called_once_with(
        None,
        restricted_account_url="https://restricted.blob.core.windows.net",
        shared_account_url="https://shared.blob.core.windows.net",
    )

    # Dataset was staged from the input container.
    fake_blob.download_blob.assert_called_once()
    assert fake_blob.download_blob.call_args.args[0] == "input"

    # Outputs published with the results/debug split.
    dests = {call.args[0]: call.args[1] for call in fake_blob.upload_file.call_args_list}
    assert dests["output"] == "summarisation/standard/run1/summary.json"
    debug_blobs = {call.args[1] for call in fake_blob.upload_file.call_args_list if call.args[0] == "debug"}
    assert "summarisation/standard/run1/results.jsonl" in debug_blobs
    assert "summarisation/standard/run1/hallucination_inputs.json" in debug_blobs
    # The threshold-based review lands in the debug bucket alongside the per-entry data.
    assert "summarisation/standard/run1/threshold_review.json" in debug_blobs


def test_halted_run_publishes_then_fails_pipeline(tmp_path: Path) -> None:
    """A halted run must still publish its summary to blob, then exit non-zero."""
    config = _write_config(tmp_path)
    fake_blob = MagicMock()
    halted_summary = {"errors": [{"stage": "evaluate", "error": "halted before completion: RuntimeError: 401"}]}

    with (
        patch("evals.summarisation.src.main.EvalBlobStorage.from_account_urls", return_value=fake_blob),
        patch("evals.summarisation.src.optimisation.run_eval", side_effect=_make_fake_run_eval(halted_summary)),
    ):
        result = runner.invoke(app, ["--config", str(config)])

    # Pipeline fails...
    assert result.exit_code == 1, result.output
    # ...but the summary explaining the failure was published to blob first.
    dests = {call.args[0]: call.args[1] for call in fake_blob.upload_file.call_args_list}
    assert dests["output"] == "summarisation/standard/run1/summary.json"


def test_threshold_failure_publishes_then_fails_pipeline(tmp_path: Path) -> None:
    config = _write_config(tmp_path)
    fake_blob = MagicMock()
    threshold_review = {"overall_passed": False}

    with (
        patch("evals.summarisation.src.main.EvalBlobStorage.from_account_url", return_value=fake_blob),
        patch(
            "evals.summarisation.src.optimisation.run_eval",
            side_effect=_make_fake_run_eval({}, threshold_review),
        ),
    ):
        result = runner.invoke(app, ["--config", str(config)])

    assert result.exit_code == 1, result.output
    assert "Eval thresholds breached" in result.output
    dests = {call.args[0]: call.args[1] for call in fake_blob.upload_file.call_args_list}
    assert dests["output"] == "summarisation/standard/run1/summary.json"
    debug_blobs = {call.args[1] for call in fake_blob.upload_file.call_args_list if call.args[0] == "debug"}
    assert "summarisation/standard/run1/threshold_review.json" in debug_blobs


def test_results_artifact_contains_only_summary_when_blob_upload_fails(tmp_path: Path) -> None:
    config = _write_config(tmp_path)
    artifact_dir = tmp_path / "artifact"
    fake_blob = MagicMock()
    fake_blob.upload_file.side_effect = RuntimeError("upload failed")

    with (
        patch("evals.summarisation.src.main.EvalBlobStorage.from_account_url", return_value=fake_blob),
        patch("evals.summarisation.src.optimisation.run_eval", side_effect=_fake_run_eval),
    ):
        result = runner.invoke(app, ["--config", str(config), "--results-artifact-dir", str(artifact_dir)])

    assert result.exit_code != 0
    assert (artifact_dir / "standard" / "run1" / "summary.json").read_text(encoding="utf-8") == "{}"
    assert not (artifact_dir / "standard" / "run1" / "results.jsonl").exists()
    assert not (artifact_dir / "standard" / "run1" / "hallucination_inputs.json").exists()
    assert not (artifact_dir / "standard" / "run1" / "threshold_review.json").exists()
