from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import TypedDict

from pydantic import BaseModel, Field

from evals.summarisation.src.hallucination.types import HallucinationInput


class RunSummary(TypedDict):
    run_id: str
    split: str
    n: int
    overall: float | None
    metrics: dict[str, dict[str, float]]
    # Dimensions deliberately not judged for this run's summariser template, e.g. citation quality
    # for a template that produces no citations.
    skipped_dimensions: list[str]
    timestamp: str
    latency_ms: dict[str, int]


class DialogExample(BaseModel):
    """Example containing dialogue and optional reference summary.

    Where the example is handed to a judge metric, ``dialogue`` must already be numbered by
    ``judge_transcript_text``: the judge is told its transcript is numbered and is asked to resolve
    ``[n]`` citation markers against it.
    """

    example_id: str
    dialogue: str
    reference_summary: str | None = None


class GenerationConfig(BaseModel):
    """Configuration for LLM generation parameters."""

    temperature: float
    max_tokens: int


class DialogSummary(BaseModel):
    """Generated summary with model and generation metadata."""

    summary: str
    model: str
    prompt_version: str
    generation_config: GenerationConfig


class MetricResult(BaseModel):
    """Result from a single metric evaluation with score and reason."""

    score: float = Field(ge=0, le=5)
    reason: str


class EvalRecord(BaseModel):
    """Complete evaluation record for a single example, with flexible fields matching current usage."""

    run_id: str | None = None
    timestamp: datetime | None = Field(default_factory=lambda: datetime.now(tz=UTC))
    example: DialogExample | None = None
    candidate: DialogSummary | None = None
    metrics: dict[str, MetricResult] | None = None
    latency_ms: dict[str, int] | None = None
    error: dict[str, str] | None = None
    example_id: str | None = None
    dialogue: str | None = None
    reference_summary: str | None = None
    needs_review: bool | None = None
    review_reasons: list[str] | None = None

    class Config:
        arbitrary_types_allowed = True


class EvalRunState(BaseModel):
    """Runtime state for an evaluation run (non-persisted)."""

    records: list[EvalRecord] = Field(default_factory=list)
    hallucination_inputs: list[HallucinationInput] = Field(default_factory=list)
    summarize_ms_values: list[int] = Field(default_factory=list)
    judge_ms_values: list[int] = Field(default_factory=list)
    metric_scores: dict[str, list[float]] = Field(default_factory=lambda: defaultdict(list))  # type: ignore[arg-type]
