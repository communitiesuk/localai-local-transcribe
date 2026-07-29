"""Auditability is only judged for summary paths that can actually produce citations.

``auditability`` scores citation quality, so it is meaningless for a template configured without
the citation pipeline (``citations_required = False``) or for the basic-minutes fallback, which has
no citation step at all. Scoring it anyway produced a number that said nothing about the summary:
before the judge was grounded it invented markers and scored 4.2/5, and once grounded it scored a
flat 3.0 — a constant, not a measurement. The dimension is skipped for those paths instead.
"""

from __future__ import annotations

import orjson
import pytest

from common.services.template_manager import TemplateNotFoundError
from evals.summarisation.src.common import build_metrics
from evals.summarisation.src.common.metric import CITATION_DIMENSION, judged_dimensions, template_supports_citations


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


def test_judged_dimensions_rejects_an_unknown_template_even_without_auditability():
    """The template name is resolved on every call, so a typo fails before any LLM call is made."""
    with pytest.raises(TemplateNotFoundError):
        judged_dimensions(["accuracy"], "No Such Template")


def test_judged_dimensions_drops_auditability_for_a_non_citing_template():
    dimensions = judged_dimensions(["accuracy", CITATION_DIMENSION], "Short 'n' Sweet")

    assert dimensions == ["accuracy"]


def test_build_metrics_drops_auditability_for_a_non_citing_template(eval_config):
    """The bias eval builds its judge metrics from config; the same rule has to apply there."""
    cfg = eval_config(template_name="Short 'n' Sweet", metrics=["accuracy", CITATION_DIMENSION])

    assert [m.criterion for m in build_metrics(cfg)] == ["accuracy"]


# --- standard eval ---


def test_standard_eval_skips_auditability_for_a_non_citing_template(eval_config, run_standard_eval, judge_scoring_5):
    judge = judge_scoring_5(["accuracy"])

    summary_path = run_standard_eval(eval_config(template_name="Short 'n' Sweet"), judge=judge)

    assert CITATION_DIMENSION not in judge.await_args.kwargs["dimensions"]

    summary = orjson.loads(summary_path.read_bytes())
    assert f"rubric_{CITATION_DIMENSION}" not in summary["metrics"]
    assert summary["skipped_dimensions"] == [CITATION_DIMENSION]


def test_standard_eval_judges_auditability_for_a_citing_template(eval_config, run_standard_eval, judge_scoring_5):
    judge = judge_scoring_5([CITATION_DIMENSION])

    summary_path = run_standard_eval(eval_config(template_name="General"), judge=judge)

    assert CITATION_DIMENSION in judge.await_args.kwargs["dimensions"]
    assert orjson.loads(summary_path.read_bytes())["skipped_dimensions"] == []
