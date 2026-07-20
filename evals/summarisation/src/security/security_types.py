from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from common.database.postgres_models import DialogueEntry
from evals.summarisation.src.common.schemas import MetricResult


class InjectionLevel(str, Enum):
    """Severity of the instruction injected into a scenario transcript."""

    BENIGN = "benign"
    BORDERLINE = "borderline"
    MALICIOUS = "malicious"


class SecurityScenarioInput(BaseModel):
    """A single prompt-injection scenario.

    Two attack vectors share this shape, distinguished by ``template_content``:

    - **Transcript vector** (``template_content`` unset): the injection lives inside
      ``dialogue_entries`` and the scenario is summarised with the configured registered template.
    - **Custom-template vector** (``template_content`` set): the injection lives in a user-supplied
      custom template; ``dialogue_entries`` hold a clean meeting and the summariser is driven through
      the user-template path with ``template_content`` embedded verbatim.
    """

    scenario_id: str
    base_transcript: str
    injection_level: InjectionLevel
    intended_solicitation: str
    dialogue_entries: list[DialogueEntry]
    template_content: str | None = None

    @field_validator("template_content")
    @classmethod
    def _reject_empty_template_content(cls, v: str | None) -> str | None:
        """Guard the vector-routing seam: an empty/whitespace string is neither vector.

        Routing keys on ``template_content is None`` (``runner._summarise_scenario``), so a falsy-but-
        not-None value like ``""`` would silently take the custom-template path with an empty template
        and drop the registered template name. Force authors to use ``None`` for the transcript vector.
        """
        if v is not None and not v.strip():
            msg = "template_content must be non-empty when set; use null for the transcript vector"
            raise ValueError(msg)
        return v


class SecurityEvalRecord(BaseModel):
    """Complete evaluation record for a single injection scenario."""

    scenario_id: str
    injection_level: InjectionLevel
    intended_solicitation: str
    summary_text: str
    metrics: dict[str, MetricResult] = Field(default_factory=dict)
    error: str | None = None
    content_safety_blocked: bool = False


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
    n_failed: int = 0
    by_level: dict[str, LevelRollup] = Field(default_factory=dict)
