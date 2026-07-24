from __future__ import annotations

import pytest

from evals.summarisation.src.common import AppConfig
from evals.summarisation.src.optimisation.runner import _load_rows_from_jsonl, load_dspy_devset


def _blob_cfg() -> AppConfig:
    return AppConfig.model_validate(
        {
            "run": {"eval_type": "standard", "output_dir": "out"},
            "dataset": {
                "name": "synthetic",
                "source": "blob",
                "blob_path": "summarisation/standard/d.jsonl",
            },
            "judge": {"pass_threshold": 4},
            "prompts": {"judge_template_path": "prompts/judge.j2"},
        }
    )


def test_load_rows_from_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "d.jsonl"
    path.write_text(
        '{"id": "1", "dialogue": "a", "summary": "s1"}\n\n{"id": "2", "dialogue": "b", "summary": "s2"}\n',
        encoding="utf-8",
    )

    rows = _load_rows_from_jsonl(path, limit=None)

    assert [r["id"] for r in rows] == ["1", "2"]


def test_load_rows_from_jsonl_honours_limit(tmp_path):
    path = tmp_path / "d.jsonl"
    path.write_text(
        '{"id": "1", "dialogue": "a", "summary": "s1"}\n{"id": "2", "dialogue": "b", "summary": "s2"}\n',
        encoding="utf-8",
    )

    rows = _load_rows_from_jsonl(path, limit=1)

    assert len(rows) == 1


def test_load_dspy_devset_from_blob_jsonl(tmp_path):
    path = tmp_path / "d.jsonl"
    path.write_text(
        '{"id": "x1", "dialogue": "#A#: Hi.", "summary": "greeting"}\n'
        '{"id": "x2", "dialogue": "#A#: Bye.", "summary": "farewell"}\n',
        encoding="utf-8",
    )

    devset = load_dspy_devset(_blob_cfg(), split="test", limit=None, dataset_path=path)

    assert len(devset) == 2
    assert devset[0].example_id == "x1"
    assert devset[0].dialogue == "#A#: Hi."
    assert devset[0].reference_summary == "greeting"
    assert "dialogue" in devset[0].inputs()


def test_load_dspy_devset_blob_requires_dataset_path():
    with pytest.raises(ValueError, match="dataset_path"):
        load_dspy_devset(_blob_cfg(), split="test", limit=None, dataset_path=None)
