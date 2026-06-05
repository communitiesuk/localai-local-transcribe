from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DialogExample(BaseModel):
    """Example containing dialogue and optional reference summary."""

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


CriteriaName = Literal["faithfulness", "coverage", "conciseness", "coherence"]


class MetricResult(BaseModel):
    """Result from a single metric evaluation with score and reason."""

    score: float = Field(ge=1, le=5)
    reason: str


class EvalRecord(BaseModel):
    """Complete evaluation record for a single example, with flexible fields matching current usage."""

    # Core fields (optional for backward compatibility)
    run_id: str | None = None
    timestamp: datetime | None = None
    example: DialogExample | None = None
    candidate: DialogSummary | None = None
    metrics: dict[str, MetricResult] | None = None
    latency_ms: dict[str, int] | None = None
    error: dict[str, str] | None = None

    # Additional fields used by the refactored runner
    example_id: str | None = None
    dialogue: str | None = None
    reference_summary: str | None = None
    needs_review: bool | None = None
    review_reasons: list[str] | None = None

    class Config:
        arbitrary_types_allowed = True
from collections import defaultdict
from typing import List, Dict

from ..hallucination.types import HallucinationInput

class EvalRunState(BaseModel):
    """Runtime state for an evaluation run (non‑persisted)."""

    records: List[EvalRecord] = Field(default_factory=list)
    hallucination_inputs: List[HallucinationInput] = Field(default_factory=list)
    summarize_ms_values: List[int] = Field(default_factory=list)
    judge_ms_values: List[int] = Field(default_factory=list)
    metric_scores: Dict[str, List[float]] = Field(default_factory=lambda: defaultdict(list))
