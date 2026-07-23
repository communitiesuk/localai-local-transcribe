"""
Tests the hallucination eval CLI's exit code: non-zero when any summary fails the
claim citation rate threshold, zero otherwise, driven through the Typer app with the
standard eval and hallucination runner mocked.

Exercises: evals.summarisation.src.main.app (hallucination exit-code path).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import orjson
import yaml
from typer.testing import CliRunner

from evals.summarisation.src.hallucination.constants import RESULTS_FILENAME, SUMMARY_FILENAME
from evals.summarisation.src.hallucination.types import HallucinationInput
from evals.summarisation.src.main import app

runner = CliRunner()


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "run": {
            "eval_type": "standard",
            "output_dir": str(tmp_path / "output"),
            "prompt_version": "dev",
            "limit": 1,
        },
        "dataset": {"name": "knkarthick/dialogsum", "dialogue_field": "dialogue", "reference_summary_field": "summary"},
        "judge": {"pass_threshold": 4},
        "metrics": ["accuracy"],
        "prompts": {
            "summarizer_template_name": "General",
            "judge_template_path": "evals/summarisation/prompts/judge.j2",
        },
        "hallucination": {"enabled": True},
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def _fake_hallucination_factory(*, n_fail: int):
    def _fake_run(cfg, inputs, output_dir):  # noqa: ARG001
        run_id = "test"
        run_dir = Path(output_dir) / run_id
        run_dir.parent.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / RESULTS_FILENAME).write_bytes(b"")
        summary = {"citation_outcomes": {"pass": 1, "review": 0, "fail": n_fail}}
        (run_dir / SUMMARY_FILENAME).write_bytes(orjson.dumps(summary))
        return run_id, run_dir / RESULTS_FILENAME

    return _fake_run


def _run(tmp_path: Path, *, n_fail: int):
    config = _write_config(tmp_path)
    stub_inputs = [HallucinationInput(example_id="e", hypothesis_model="m", summary_html="<p>x</p>")]
    with (
        patch("evals.summarisation.src.main.run_standard_eval", return_value=stub_inputs),
        patch(
            "evals.summarisation.src.hallucination.run_hallucination_eval",
            new=_fake_hallucination_factory(n_fail=n_fail),
        ),
    ):
        return runner.invoke(app, ["--config", str(config)])


def test_cli_exits_1_when_a_summary_fails_the_gate(tmp_path):
    assert _run(tmp_path, n_fail=1).exit_code == 1


def test_cli_exits_0_when_no_summary_fails_the_gate(tmp_path):
    assert _run(tmp_path, n_fail=0).exit_code == 0
