from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.common.schemas import MetricResult


class InjectionLevel(str, Enum):
    """Severity of the instruction injected into a scenario transcript."""

    BENIGN = "benign"
    BORDERLINE = "borderline"
    MALICIOUS = "malicious"


class SecurityScenarioInput(BaseModel):
    """A single prompt-injection scenario: a base transcript with an injected instruction."""

    scenario_id: str
    base_transcript: str
    injection_level: InjectionLevel
    intended_solicitation: str
    dialogue_entries: list[DialogueEntry]


class SecurityEvalRecord(BaseModel):
    """Complete evaluation record for a single injection scenario."""

    scenario_id: str
    injection_level: InjectionLevel
    intended_solicitation: str
    summary_text: str
    metrics: dict[str, MetricResult] = Field(default_factory=dict)
    error: str | None = None


class LevelRollup(BaseModel):
    """Aggregate judge scores for one injection level."""

    n: int
    dimension_means: dict[str, float] = Field(default_factory=dict)


class SecurityRunSummary(BaseModel):
    """Aggregated summary of a security evaluation run.

    Scores are rolled up per injection level only; dimensions are routed per level (see
    ``SECURITY_DIMENSIONS_BY_LEVEL``), so a single run-wide mean per dimension would average
    different-sized populations and mislead.
    """

    run_id: str
    timestamp: str
    n_scenarios: int
    by_level: dict[str, LevelRollup] = Field(default_factory=dict)
