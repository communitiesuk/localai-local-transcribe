"""Auditability is only judged for summary paths that can actually produce citations.

``auditability`` scores citation quality, so it is meaningless for a template configured without
the citation pipeline (``citations_required = False``) or for the basic-minutes fallback, which has
no citation step at all. Scoring it anyway produced a number that said nothing about the summary:
before the judge was grounded it invented markers and scored 4.2/5, and once grounded it scored a
flat 3.0 — a constant, not a measurement. The dimension is skipped for those paths instead.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import orjson
import pytest

from common.services.template_manager import TemplateNotFoundError
from evals.summarisation.src.common import AppConfig, build_metrics
from evals.summarisation.src.common.metric import CITATION_DIMENSION, judged_dimensions, template_supports_citations
from evals.summarisation.src.optimisation.runner import run_eval


@pytest.mark.parametrize(
    ("template_name", "supported"),
    [
        ("General", True),
        ("Care Assessment V2", True),
        ("Delivery", True),
        ("Short 'n' Sweet", False),
        (None, False),  # no template: the basic-minutes fallback, which never cites
    ],
)
def test_template_supports_citations(template_name, supported):
    assert template_supports_citations(template_name) is supported


def test_template_supports_citations_rejects_unknown_template():
    """A mistyped template name must fail loudly, not silently skip the dimension."""
    with pytest.raises(TemplateNotFoundError):
        template_supports_citations("No Such Template")


def test_judged_dimensions_keeps_auditability_for_a_citing_template():
    dimensions = judged_dimensions(["accuracy", CITATION_DIMENSION], "General")

    assert dimensions == ["accuracy", CITATION_DIMENSION]


def test_judged_dimensions_drops_auditability_for_a_non_citing_template():
    dimensions = judged_dimensions(["accuracy", CITATION_DIMENSION], "Short 'n' Sweet")

    assert dimensions == ["accuracy"]


def test_build_metrics_drops_auditability_for_a_non_citing_template(tmp_path):
    """The bias eval builds its judge metrics from config; the same rule has to apply there."""
    cfg = _cfg(tmp_path, template_name="Short 'n' Sweet", metrics=["accuracy", CITATION_DIMENSION])

    assert [m.criterion for m in build_metrics(cfg)] == ["accuracy"]


# --- standard eval ---


def _cfg(tmp_path: Path, *, template_name: str | None, **overrides: object) -> AppConfig:
    return AppConfig.model_validate(
        {
            "run": {"output_dir": str(tmp_path / "output")},
            "dataset": {"name": "d", "dialogue_field": "dialogue", "reference_summary_field": "summary"},
            "judge": {"pass_threshold": 4},
            "prompts": {
                "judge_template_path": "prompts/judge.jinja2",
                "summarizer_template_name": template_name,
            },
            **overrides,
        }
    )


def _run(cfg: AppConfig, judge: AsyncMock) -> Path:
    mock_rows = [{"id": "1", "dialogue": "#A#: We agreed the deadline.", "summary": "Deadline agreed"}]
    mock_split = Mock()
    mock_split.select = Mock(return_value=mock_rows)
    mock_split.__len__ = Mock(return_value=1)

    generated = Mock(text="Deadline agreed.", hallucinations=[], total_claims=0)

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

        _run_id, _results, summary_path, _h = run_eval(cfg, split="test", limit=1, prompt_version="v1")

    return summary_path


def _judge_returning(dimensions: list[str]) -> AsyncMock:
    return AsyncMock(
        return_value={"dimensions": {d: {"score": "5", "rationale": "fine"} for d in dimensions}},
    )


def test_standard_eval_skips_auditability_for_a_non_citing_template(tmp_path):
    judge = _judge_returning(["accuracy"])

    summary_path = _run(_cfg(tmp_path, template_name="Short 'n' Sweet"), judge)

    assert CITATION_DIMENSION not in judge.await_args.kwargs["dimensions"]

    summary = orjson.loads(summary_path.read_bytes())
    assert f"rubric_{CITATION_DIMENSION}" not in summary["metrics"]
    assert summary["skipped_dimensions"] == [CITATION_DIMENSION]


def test_standard_eval_judges_auditability_for_a_citing_template(tmp_path):
    judge = _judge_returning([CITATION_DIMENSION])

    summary_path = _run(_cfg(tmp_path, template_name="General"), judge)

    assert CITATION_DIMENSION in judge.await_args.kwargs["dimensions"]
    assert orjson.loads(summary_path.read_bytes())["skipped_dimensions"] == []
