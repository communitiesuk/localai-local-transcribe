from __future__ import annotations

import logging
from pathlib import Path

import yaml

from evals.summarisation.src.bias.bias_types import ComparisonMetrics
from evals.summarisation.src.bias.constants import SPC_BASELINE_FILENAME, SPC_SIGMA
from evals.summarisation.src.bias.spc_types import SPCBaseline, SPCBaselineStat, SPCCheck

logger = logging.getLogger(__name__)


def load_spc_baseline(input_dir: Path) -> SPCBaseline:
    """Loads the SPC baseline stashed alongside the inputs.

    The baseline lives at ``<input_dir>/spc_baseline.yaml``. A missing file is a
    graceful skip: an empty baseline is returned and control-chart checks emit no
    verdicts. A present-but-malformed file still raises, since that is a genuine
    error rather than a deliberate absence.
    """
    path = input_dir / SPC_BASELINE_FILENAME
    if not path.exists():
        logger.warning(
            "No SPC baseline found at %s; skipping control-chart checks (SPC verdicts will be empty)",
            path,
        )
        return SPCBaseline(metrics={})
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    baseline = SPCBaseline.model_validate(data)
    logger.info("Loaded SPC baseline with %d metric(s) at sigma=%s", len(baseline.metrics), SPC_SIGMA)
    return baseline


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
