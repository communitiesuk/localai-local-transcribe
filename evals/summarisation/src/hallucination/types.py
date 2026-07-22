from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SupportLabel = Literal["Supported", "Unsupported", "Partial"]


class ClassifiedStatement(BaseModel):
    hallucination_text: str
    citation_indices: list[int]
    hallucination_type: SupportLabel
    hallucination_reason: str


class HallucinationReport(BaseModel):
    run_id: str
    example_id: str
    hypothesis_model: str
    template_name: str | None
    timestamp: datetime
    prompt_version: str
    statements: list[ClassifiedStatement]
    metrics: dict[str, int | float | bool | str]


class HallucinationInput(BaseModel):
    example_id: str
    hypothesis_model: str
    summary_html: str
    uncited_claims: list[str] = Field(default_factory=list)
    total_claims: int = 0
