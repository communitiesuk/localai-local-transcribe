from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from evals.shared.blob_io import (
    output_prefix_for,
    publish_run_outputs,
    stage_dataset,
)

RESULTS = frozenset({"summary.json"})


def test_output_prefix_for_uses_eval_type_and_subtype() -> None:
    assert output_prefix_for("summarisation", "standard", "run1") == "summarisation/standard/run1"
    assert (
        output_prefix_for("summarisation", "standard", "run1", subtype="hallucination")
        == "summarisation/hallucination/run1"
    )


def test_output_prefix_for_without_base_prefix() -> None:
    assert output_prefix_for("", "standard", "run1") == "standard/run1"


def test_stage_dataset_downloads_blob_path(tmp_path: Path) -> None:
    blob = MagicMock()
    blob.download_blob.return_value = tmp_path / "d.jsonl"

    result = stage_dataset(blob, "summarisation/standard/d.jsonl", tmp_path)

    blob.download_blob.assert_called_once_with("input", "summarisation/standard/d.jsonl", tmp_path / "d.jsonl")
    assert result == tmp_path / "d.jsonl"


def test_stage_dataset_requires_blob_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="blob_path"):
        stage_dataset(MagicMock(), None, tmp_path)


def _publish(blob: Any, run_dir: Path, run_id: str, **kwargs: Any) -> dict[str, str]:
    return publish_run_outputs(
        blob,
        run_dir,
        run_id,
        output_prefix="summarisation",
        eval_type="standard",
        results_relative_paths=RESULTS,
        **kwargs,
    )


def test_publish_run_outputs_splits_results_from_debug(tmp_path: Path) -> None:
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")
    (run_dir / "results.jsonl").write_text("{}\n", encoding="utf-8")
    (run_dir / "hallucination_inputs.json").write_text("[]", encoding="utf-8")

    blob = MagicMock()
    published = _publish(blob, run_dir, "run1")

    # summary.json -> results container; everything else -> debug container.
    assert published["summary.json"] == "output/summarisation/standard/run1/summary.json"
    assert published["results.jsonl"] == "debug/summarisation/standard/run1/results.jsonl"
    assert published["hallucination_inputs.json"] == "debug/summarisation/standard/run1/hallucination_inputs.json"

    uploaded_containers = {call.args[0] for call in blob.upload_file.call_args_list}
    assert uploaded_containers == {"output", "debug"}


def test_publish_run_outputs_nested_summary_goes_to_debug(tmp_path: Path) -> None:
    # Only the top-level summary.json is the aggregate; a nested one is per-entry debug data.
    run_dir = tmp_path / "run1"
    (run_dir / "sub").mkdir(parents=True)
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")
    (run_dir / "sub" / "summary.json").write_text("{}", encoding="utf-8")

    blob = MagicMock()
    published = _publish(blob, run_dir, "run1")

    assert published["summary.json"] == "output/summarisation/standard/run1/summary.json"
    assert published["sub/summary.json"] == "debug/summarisation/standard/run1/sub/summary.json"


def test_publish_run_outputs_subtype_prefix(tmp_path: Path) -> None:
    run_dir = tmp_path / "hrun"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")

    blob = MagicMock()
    published = _publish(blob, run_dir, "hrun", subtype="hallucination")

    assert published["summary.json"] == "output/summarisation/hallucination/hrun/summary.json"
