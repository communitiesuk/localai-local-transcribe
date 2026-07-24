from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from evals.summarisation.src.common import AppConfig
from evals.summarisation.src.common.blob_io import (
    output_prefix_for,
    publish_run_outputs,
    stage_dataset,
)


def _cfg(**overrides) -> AppConfig:
    base = {
        "run": {"eval_type": "standard", "output_dir": "out"},
        "dataset": {"name": "synthetic"},
        "judge": {"pass_threshold": 4},
        "prompts": {"judge_template_path": "prompts/judge.j2"},
        "blob": {"enabled": True},
    }
    base.update(overrides)
    return AppConfig.model_validate(base)


def test_output_prefix_for_uses_eval_type_and_subtype():
    cfg = _cfg(run={"eval_type": "standard", "output_dir": "out"})
    assert output_prefix_for(cfg, "run1") == "summarisation/standard/run1"
    assert output_prefix_for(cfg, "run1", subtype="hallucination") == "summarisation/hallucination/run1"


def test_stage_dataset_downloads_blob_path(tmp_path):
    cfg = _cfg(dataset={"name": "synthetic", "source": "blob", "blob_path": "summarisation/standard/d.jsonl"})
    blob = MagicMock()
    blob.download_blob.return_value = tmp_path / "d.jsonl"

    result = stage_dataset(cfg, blob, tmp_path)

    blob.download_blob.assert_called_once_with("input", "summarisation/standard/d.jsonl", tmp_path / "d.jsonl")
    assert result == tmp_path / "d.jsonl"


def test_stage_dataset_requires_blob_path(tmp_path):
    cfg = _cfg(dataset={"name": "synthetic", "source": "blob"})
    with pytest.raises(ValueError, match="blob_path"):
        stage_dataset(cfg, MagicMock(), tmp_path)


def test_publish_run_outputs_splits_results_from_debug(tmp_path):
    cfg = _cfg()
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")
    (run_dir / "results.jsonl").write_text("{}\n", encoding="utf-8")
    (run_dir / "hallucination_inputs.json").write_text("[]", encoding="utf-8")

    blob = MagicMock()
    published = publish_run_outputs(cfg, blob, run_dir, "run1")

    # summary.json -> results container; everything else -> debug container.
    assert published["summary.json"] == "output/summarisation/standard/run1/summary.json"
    assert published["results.jsonl"] == "debug/summarisation/standard/run1/results.jsonl"
    assert published["hallucination_inputs.json"] == "debug/summarisation/standard/run1/hallucination_inputs.json"

    uploaded_containers = {call.args[0] for call in blob.upload_file.call_args_list}
    assert uploaded_containers == {"output", "debug"}


def test_publish_run_outputs_subtype_prefix(tmp_path):
    cfg = _cfg()
    run_dir = tmp_path / "hrun"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")

    blob = MagicMock()
    published = publish_run_outputs(cfg, blob, run_dir, "hrun", subtype="hallucination")

    assert published["summary.json"] == "output/summarisation/hallucination/hrun/summary.json"
