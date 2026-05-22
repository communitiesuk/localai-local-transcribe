from __future__ import annotations

import uuid
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

    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    summary: str
    model: str
    prompt_version: str
    generation_config: GenerationConfig


CriteriaName = Literal["faithfulness", "coverage", "conciseness", "coherence"]


class MetricResult(BaseModel):
    """Result from a single metric evaluation with score and reason."""

    score: float = Field(..., ge=1, le=5)
    reason: str | None = None


class EvalRecord(BaseModel):
    """Complete evaluation record for a single example."""

    run_id: str
    timestamp: datetime
    example: DialogExample
    candidate: DialogSummary
    metrics: dict[str, MetricResult]
    latency_ms: dict[str, int]
    error: dict[str, str] | None = None
