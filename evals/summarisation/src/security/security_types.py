from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.common.schemas import MetricResult

InjectionLevel = Literal["benign", "borderline", "malicious"]


class SecurityScenarioInput(BaseModel):
    """A single prompt-injection scenario: a base transcript with an injected instruction.

    Reuses the production ``DialogueEntry`` shape so the scenario can be fed straight into the
    existing summariser via ``generate_summary``.
    """

    scenario_id: str
    base_transcript: str
    injection_level: InjectionLevel
    intended_solicitation: str = Field(
        description="What the injected instruction is trying to make the summariser do, and why."
    )
    dialogue_entries: list[DialogueEntry]


class SecurityEvalRecord(BaseModel):
    """Complete evaluation record for a single injection scenario."""

    run_id: str
    scenario_id: str
    base_transcript: str
    injection_level: InjectionLevel
    intended_solicitation: str
    summary_text: str
    metrics: dict[str, MetricResult] = Field(default_factory=dict)
    error: dict[str, str] | None = None


class LevelRollup(BaseModel):
    """Aggregate judge scores for one injection level."""

    n: int
    dimension_means: dict[str, float] = Field(default_factory=dict)


class SecurityRunSummary(BaseModel):
    """Aggregated summary of a security evaluation run."""

    run_id: str
    timestamp: str
    n_scenarios: int
    dimension_means: dict[str, float] = Field(default_factory=dict)
    by_level: dict[str, LevelRollup] = Field(default_factory=dict)
