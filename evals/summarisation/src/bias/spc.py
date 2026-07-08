"""
Statistical Process Control checks: loads a per-metric baseline (mean/std) and
tests each factual-vs-counterfactual delta against mean ± SPC_SIGMA*std control
limits. A delta narrowed toward zero on the same side passes; a sign reversal or
a breach of the limits alerts.

Pipeline: one of the two bias thresholds; invoked by thresholds.apply_thresholds
per comparison.

Depends on: bias/bias_types (ComparisonMetrics), bias/constants
(SPC_BASELINE_FILENAME, SPC_SIGMA), bias/spc_types.
Depended on by: bias/thresholds.py, bias/runner.py, bias/bias_types.py.
"""

from __future__ import annotations

import logging
import statistics
from pathlib import Path

import yaml

from evals.summarisation.src.bias.bias_types import ComparisonMetrics, ComparisonResult
from evals.summarisation.src.bias.constants import MIN_BASELINE_OBSERVATIONS, SPC_BASELINE_FILENAME, SPC_SIGMA
from evals.summarisation.src.bias.spc_types import SPCBaseline, SPCBaselineStat, SPCCheck

logger = logging.getLogger(__name__)


def load_spc_baseline(input_dir: Path) -> SPCBaseline:
    """Loads the SPC baseline stashed alongside the inputs.

    The baseline lives at ``<input_dir>/spc_baseline.yaml`` and is a required
    input: a missing file raises, since control-chart checks cannot run without
    it.
    """
    path = input_dir / SPC_BASELINE_FILENAME
    if not path.exists():
        msg = f"SPC baseline not found at {path}; it is a required input for control-chart checks"
        raise FileNotFoundError(msg)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    baseline = SPCBaseline.model_validate(data)
    logger.info("Loaded SPC baseline with %d metric(s) at sigma=%s", len(baseline.metrics), SPC_SIGMA)
    return baseline


def build_spc_baseline(comparisons: list[ComparisonResult], description: str | None = None) -> SPCBaseline:
    """Derives an SPC baseline from a completed run's comparisons.

    Records the mean and standard deviation of each metric's factual-vs-counterfactual
    delta across ``comparisons`` — the "baseline period" of ADR-024 — so a later run can
    check its deltas against these control limits. Each comparison contributes one delta
    per metric (already averaged over its iterations), so a metric's observation count is
    its number of comparisons. A metric is skipped (with a warning) when it has fewer than
    ``MIN_BASELINE_OBSERVATIONS`` comparisons or zero variance, since neither yields a
    usable control band.
    """
    deltas: dict[str, list[float]] = {}
    for comparison in comparisons:
        for metric in comparison.metrics:
            deltas.setdefault(metric.metric_name, []).append(metric.delta)

    stats: dict[str, SPCBaselineStat] = {}
    for metric_name, values in deltas.items():
        if len(values) < MIN_BASELINE_OBSERVATIONS:
            logger.warning(
                "SPC baseline: skipping %r (%d observation(s), need >=%d)",
                metric_name,
                len(values),
                MIN_BASELINE_OBSERVATIONS,
            )
            continue
        std = statistics.stdev(values)
        if std <= 0.0:
            logger.warning("SPC baseline: skipping %r (zero variance across observations)", metric_name)
            continue
        stats[metric_name] = SPCBaselineStat(mean=statistics.mean(values), std=std)

    if not stats:
        msg = "Cannot build an SPC baseline: no metric had >=2 observations with non-zero variance"
        raise ValueError(msg)

    logger.info("Built SPC baseline over %d comparison(s) with %d metric(s)", len(comparisons), len(stats))
    return SPCBaseline(description=description, metrics=stats)


def save_spc_baseline(baseline: SPCBaseline, output_dir: Path) -> Path:
    """Writes the baseline as ``spc_baseline.yaml`` under ``output_dir`` and returns its path.

    The file is written in the same shape ``load_spc_baseline`` expects, so it can be
    copied into a future run's input directory to drive control-chart checks.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / SPC_BASELINE_FILENAME
    path.write_text(yaml.safe_dump(baseline.model_dump(), sort_keys=False), encoding="utf-8")
    logger.info("SPC baseline written to %s (%d metric(s))", path, len(baseline.metrics))
    return path


def _narrowed_toward_zero(delta: float, mean: float) -> bool:
    """True when ``delta`` sits between zero and the baseline mean.

    This is the only out-of-limits case that counts as a pass: the gap has
    shrunk toward zero *without changing side*. A sign reversal (delta and mean
    on opposite sides of zero) is deliberately excluded — a reversal in direction
    is an alert, not an improvement.
    """
    if mean >= 0:
        return 0.0 <= delta <= mean
    return mean <= delta <= 0.0


def check_metric(metric_name: str, delta: float, baseline: SPCBaseline) -> SPCCheck | None:
    """Checks a single metric's delta against the baseline control limits.

    Returns None when the metric has no baseline entry — there is nothing to
    check, so no verdict is emitted.
    """
    stat: SPCBaselineStat | None = baseline.metrics.get(metric_name)
    if stat is None:
        return None

    half_width = SPC_SIGMA * stat.std
    lower_limit = stat.mean - half_width
    upper_limit = stat.mean + half_width
    within_limits = lower_limit <= delta <= upper_limit
    passed = within_limits or _narrowed_toward_zero(delta, stat.mean)

    return SPCCheck(
        metric_name=metric_name,
        delta=delta,
        baseline_mean=stat.mean,
        baseline_std=stat.std,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
        passed=passed,
    )


def evaluate_spc(metrics: list[ComparisonMetrics], baseline: SPCBaseline) -> list[SPCCheck]:
    """Runs the control-chart check for every metric that has a baseline entry."""
    return [
        check for metric in metrics if (check := check_metric(metric.metric_name, metric.delta, baseline)) is not None
    ]
