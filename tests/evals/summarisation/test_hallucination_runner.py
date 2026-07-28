from __future__ import annotations

import json
from pathlib import Path

import orjson

from common.settings import get_settings
from evals.summarisation.src.common.config import (
    AppConfig,
    DatasetConfig,
    JudgeConfig,
    PromptConfig,
    RunConfig,
)
from evals.summarisation.src.hallucination.constants import RESULTS_FILENAME, SUMMARY_FILENAME
from evals.summarisation.src.hallucination.runner import run_hallucination_eval
from evals.summarisation.src.hallucination.types import HallucinationInput


def _config(output_dir: Path) -> AppConfig:
    return AppConfig(
        run=RunConfig(output_dir=str(output_dir), prompt_version="dev", dataset_version="v1"),
        dataset=DatasetConfig(name="ds"),
        judge=JudgeConfig(),
        prompts=PromptConfig(summarizer_template_name="General", judge_template_path="unused"),
    )


def _read_outcomes_by_example(results_path: Path) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for line in results_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        outcomes[record["example_id"]] = record["metrics"]["citation_outcome"]
    return outcomes


def _input(example_id: str, n_uncited: int, total_claims: int) -> HallucinationInput:
    return HallucinationInput(
        example_id=example_id,
        hypothesis_model=get_settings().BEST_LLM_MODEL_NAME,
        summary_html="s",
        uncited_claims=[f"claim-{i}" for i in range(n_uncited)],
        total_claims=total_claims,
    )


def test_runner_routes_each_example_and_rolls_up_outcomes(tmp_path: Path) -> None:
    inputs = [
        _input("pass", n_uncited=1, total_claims=20),  # 19/20 = 0.95 supported -> pass boundary
        _input("review", n_uncited=3, total_claims=20),  # 17/20 = 0.85 supported -> review boundary
        _input("fail", n_uncited=5, total_claims=20),  # 15/20 = 0.75 supported -> fail
        _input("zero", n_uncited=0, total_claims=0),  # no extracted claims -> review, never a pass
    ]

    run_id, results_path = run_hallucination_eval(_config(tmp_path), inputs=inputs, output_dir=tmp_path)

    # Per-example routing lands in the results file.
    outcomes = _read_outcomes_by_example(results_path)
    assert outcomes == {"pass": "pass", "review": "review", "fail": "fail", "zero": "review"}

    # The run-level roll-up is surfaced in the summary, not just buried per row.
    summary = orjson.loads((tmp_path / run_id / SUMMARY_FILENAME).read_bytes())
    assert summary["citation_outcomes"] == {"pass": 1, "review": 2, "fail": 1}
    assert results_path == tmp_path / run_id / RESULTS_FILENAME
