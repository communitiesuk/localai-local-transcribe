from __future__ import annotations

from pydantic import BaseModel


class GroupSuccessRate(BaseModel):
    """One group's favourable-outcome rate and whether it clears 4/5 of the top-scoring group."""

    group: str
    success_rate: float
    ratio_to_advantaged: float
    passed: bool


class FourFifthsCheck(BaseModel):
    """4/5 rule across every group of a characteristic for one metric, referenced to the top-scoring group.

    ``passed`` is True only when every group clears the 4/5 threshold against the advantaged group.
    """

    protected_characteristic: str
    metric_name: str
    advantaged_group: str
    groups: list[GroupSuccessRate]
    passed: bool
