"""
Tests the bias eval CLI's exit code: non-zero when SPC or 4/5 checks fail, zero
otherwise, driven through the Typer app with the runner mocked.

Exercises: evals.summarisation.src.main.app (bias exit-code path).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import orjson
import yaml
from typer.testing import CliRunner

from evals.summarisation.src.bias.bias_types import (
    BiasEvalResults,
    ComparisonMetrics,
    ComparisonResult,
    MetricStatistics,
)
from evals.summarisation.src.bias.spc_types import SPCCheck
from evals.summarisation.src.main import app

runner = CliRunner()


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "run": {
            "eval_type": "bias",
            "input_dir": str(tmp_path / "input"),
            "output_dir": str(tmp_path / "output"),
            "prompt_version": "dev",
            "num_iterations": 1,
        },
        "dataset": {"name": "counterfactual", "dialogue_field": "dialogue", "reference_summary_field": "summary"},
        "judge": {"pass_threshold": 4},
        "metrics": ["accuracy"],
        "prompts": {
            "summarizer_template_name": "General",
            "judge_template_path": "evals/summarisation/prompts/judge.j2",
        },
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def _comparison(*, spc_passed: bool) -> ComparisonResult:
    empty = MetricStatistics(mean=0.0, std=0.0, values=[])
    check = SPCCheck(
        metric_name="sentiment",
        delta=0.9,
        baseline_mean=0.0,
        baseline_std=0.05,
        lower_limit=-0.15,
        upper_limit=0.15,
        passed=spc_passed,
    )
    return ComparisonResult(
        comparison_id="gender_male_to_female_0",
        protected_characteristic="gender",
        axis_of_change="male_to_female",
        group_a_name="Male",
        group_b_name="Female",
        metrics=[
            ComparisonMetrics(
                metric_name="sentiment",
                original_mean=0.0,
                original_std=0.0,
                counterfactual_mean=0.9,
                counterfactual_std=0.0,
                delta=0.9,
                original_values=[],
                counterfactual_values=[],
            )
        ],
        sentiment_delta=empty,
        sentiment_distribution_original=[],
        sentiment_distribution_counterfactual=[],
        spc_checks=[check],
        num_iterations=1,
        hypothesis_model="m",
        prompt_version="v",
    )


def _results(*, spc_passed: bool) -> BiasEvalResults:
    return BiasEvalResults(
        run_id="test",
        timestamp="t",
        dataset_version="v",
        engine_version="e",
        prompt_version="v",
        num_iterations=1,
        comparisons=[_comparison(spc_passed=spc_passed)],
    )


def _fake_run_factory(*, spc_passed: bool):
    async def _fake_run(cfg, input_dir, output_dir):  # noqa: ARG001
        run_id = "test"
        results_path = Path(output_dir) / run_id / "results.jsonl"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_bytes(orjson.dumps(_results(spc_passed=spc_passed).model_dump()))
        return run_id, results_path

    return _fake_run


def test_cli_exits_1_when_a_check_fails(tmp_path):
    config = _write_config(tmp_path)
    with patch(
        "evals.summarisation.src.bias.run_counterfactual_eval",
        new=AsyncMock(side_effect=_fake_run_factory(spc_passed=False)),
    ):
        result = runner.invoke(app, ["--config", str(config)])

    assert result.exit_code == 1


def test_cli_exits_0_when_all_checks_pass(tmp_path):
    config = _write_config(tmp_path)
    with patch(
        "evals.summarisation.src.bias.run_counterfactual_eval",
        new=AsyncMock(side_effect=_fake_run_factory(spc_passed=True)),
    ):
        result = runner.invoke(app, ["--config", str(config)])

    assert result.exit_code == 0
