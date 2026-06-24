from __future__ import annotations

from pydantic import BaseModel, Field


class SPCBaselineStat(BaseModel):
    """
    Baseline mean and standard deviation of the factual-vs-counterfactual delta for one metric.
    """

    mean: float
    std: float = Field(gt=0.0)


class SPCBaseline(BaseModel):
    """
    Statistical Process Control baseline.

    Holds per-metric control-chart parameters for the factual/counterfactual gap.
    Control limits are derived as ``mean ± SPC_SIGMA * std``.
    """

    description: str | None = None
    metrics: dict[str, SPCBaselineStat]


class SPCCheck(BaseModel):
    """
    Control-chart verdict for one metric's factual/counterfactual delta.

    ``passed`` is True when the delta sits within the control limits, or breaches
    a limit while narrowing toward zero (an improvement). It is False only when
    the gap widens or reverses beyond the limits.
    """

    metric_name: str
    delta: float
    baseline_mean: float
    baseline_std: float
    lower_limit: float
    upper_limit: float
    passed: bool
