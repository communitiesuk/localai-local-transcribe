"""Shared harness for driving the standard (optimisation) eval against mocked LLM calls.

``run_eval`` reaches for a dataset, a summariser and a judge, so exercising it at all means
patching the same five seams. Keeping that list here means a rename in the runner is fixed once.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from evals.summarisation.src.common import AppConfig
from evals.summarisation.src.optimisation.runner import run_eval


@pytest.fixture
def eval_config(tmp_path: Path) -> Callable[..., AppConfig]:
    """Build a minimal :class:`AppConfig` for the standard eval, writing output under ``tmp_path``."""

    def _build(*, template_name: str | None = None, metrics: list[str] | None = None) -> AppConfig:
        payload: dict = {
            "run": {"output_dir": str(tmp_path / "output")},
            "dataset": {"name": "d", "dialogue_field": "dialogue", "reference_summary_field": "summary"},
            "judge": {"pass_threshold": 4},
            "prompts": {
                "judge_template_path": "prompts/judge.jinja2",
                "summarizer_template_name": template_name,
            },
        }
        if metrics is not None:
            payload["metrics"] = metrics
        return AppConfig.model_validate(payload)

    return _build


@pytest.fixture
def run_standard_eval() -> Callable[..., Path]:
    """Run ``run_eval`` over a single mocked example and return the path to its run summary."""

    def _run(
        cfg: AppConfig,
        *,
        judge: AsyncMock,
        dialogue: str = "#A#: We agreed the deadline.",
        summary: str = "Deadline agreed.",
        total_claims: int = 0,
    ) -> Path:
        mock_split = Mock()
        mock_split.select = Mock(return_value=[{"id": "1", "dialogue": dialogue, "summary": "Deadline agreed"}])
        mock_split.__len__ = Mock(return_value=1)

        generated = Mock(text=summary, hallucinations=[], total_claims=total_claims)

        with (
            patch("evals.summarisation.src.optimisation.runner.load_dataset", return_value={"test": mock_split}),
            patch(
                "evals.summarisation.src.optimisation.runner.generate_summary",
                new_callable=AsyncMock,
                return_value=generated,
            ),
            patch("evals.summarisation.src.optimisation.runner.call_llm_judge_parallel", judge),
            patch("evals.summarisation.src.optimisation.runner.get_settings") as mock_settings,
            patch("evals.summarisation.src.optimisation.runner.tiktoken.encoding_for_model") as mock_tokenizer,
        ):
            mock_settings.return_value.FAST_LLM_MODEL_NAME = "test-model"
            mock_tokenizer.return_value.encode = Mock(return_value=[1])

            _run_id, _results, summary_path, _hallucinations = run_eval(cfg, split="test", limit=1, prompt_version="v1")

        return summary_path

    return _run


@pytest.fixture
def judge_scoring_5() -> Callable[[list[str]], AsyncMock]:
    """A judge mock that returns a top score for each of ``dimensions``."""

    def _build(dimensions: list[str]) -> AsyncMock:
        return AsyncMock(return_value={"dimensions": {d: {"score": "5", "rationale": "fine"} for d in dimensions}})

    return _build
