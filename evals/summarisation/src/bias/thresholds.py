"""
Applies the SPC and four-fifths checks to a completed bias evaluation: attaches
per-comparison verdicts to the output, logs alert summaries, and exposes
has_threshold_failures for the CLI to set its exit code.

Pipeline: post-processing step run after summarisation and judging; both checks
are pure functions of the collected records, so they can re-run without repeating
the expensive work.

Depends on: bias/bias_types, bias/four_fifths, bias/four_fifths_types, bias/spc,
bias/spc_types.
Depended on by: main.py, bias/runner.py.
"""

from __future__ import annotations

import logging

from evals.summarisation.src.bias.bias_types import BiasEvalResults, ComparisonResult, CounterfactualEvalRecord
from evals.summarisation.src.bias.four_fifths import evaluate_four_fifths
from evals.summarisation.src.bias.four_fifths_types import FourFifthsCheck
from evals.summarisation.src.bias.spc import evaluate_spc
from evals.summarisation.src.bias.spc_types import SPCBaseline

logger = logging.getLogger(__name__)


def has_threshold_failures(output: BiasEvalResults) -> bool:
    """True when any SPC or four-fifths check failed.

    Used by the CLI to set a non-zero exit code: a single breached control-chart
    limit or 4/5 disparity fails the run.
    """
    spc_failed = any(not check.passed for record in output.comparisons for check in record.spc_checks)
    four_fifths_failed = any(not check.passed for check in output.four_fifths)
    return spc_failed or four_fifths_failed


def apply_thresholds(
    output: BiasEvalResults,
    records: list[CounterfactualEvalRecord],
    baseline: SPCBaseline,
) -> None:
    """Post-processing step: attach SPC and 4/5 verdicts to an already-built output.

    Kept separate from output construction because both checks are cheap, pure
    functions of the collected records — they can be re-run over a completed
    evaluation without repeating the expensive summarisation and judging.
    """
    for record in output.comparisons:
        record.spc_checks = evaluate_spc(record.metrics, baseline)

    output.four_fifths = evaluate_four_fifths(records)

    _warn_unmatched_baseline_metrics(baseline, output.comparisons)
    _log_spc_alert_summary(output.comparisons)
    _log_four_fifths_alert_summary(output.four_fifths)


def _warn_unmatched_baseline_metrics(baseline: SPCBaseline, records: list[ComparisonResult]) -> None:
    """Warns when the baseline defines metrics that no comparison actually emits.

    A mistyped baseline key otherwise silently drops that metric's control-chart
    check without any signal.
    """
    emitted = {metric.metric_name for record in records for metric in record.metrics}
    unmatched = sorted(set(baseline.metrics) - emitted)
    if unmatched:
        logger.warning(
            "SPC baseline defines metric(s) not present in this run (check spelling): %s",
            ", ".join(unmatched),
        )


def _log_spc_alert_summary(records: list[ComparisonResult]) -> None:
    """Surfaces an aggregate count of failing control-chart checks."""
    alerts = [
        (record.comparison_id, check.metric_name)
        for record in records
        for check in record.spc_checks
        if not check.passed
    ]
    if alerts:
        logger.warning(
            "SPC: %d failing check(s) across %d comparison(s); see spc_checks in results",
            len(alerts),
            len({comparison_id for comparison_id, _ in alerts}),
        )
    else:
        logger.info("SPC: no failing checks")


def _log_four_fifths_alert_summary(checks: list[FourFifthsCheck]) -> None:
    """Surfaces an aggregate count of characteristics that fail the 4/5 rule."""
    failures = [(check.protected_characteristic, check.metric_name) for check in checks if not check.passed]
    if failures:
        logger.warning(
            "4/5 rule: %d failing check(s) across %d characteristic(s); see four_fifths in results",
            len(failures),
            len({characteristic for characteristic, _ in failures}),
        )
    else:
        logger.info("4/5 rule: no failing checks")
