from __future__ import annotations

from evals.summarisation.prompts.judge import (
    CRITICAL_DIMENSIONS,
    CRITICAL_THRESHOLD,
    DIMENSIONS,
    FAIL_THRESHOLD,
    REVIEW_THRESHOLD,
    build_system_prompt,
    build_user_message,
)
from evals.summarisation.prompts.schema_validator import validate_evaluation

__all__ = [
    "build_system_prompt",
    "build_user_message",
    "validate_evaluation",
    "DIMENSIONS",
    "CRITICAL_DIMENSIONS",
    "CRITICAL_THRESHOLD",
    "REVIEW_THRESHOLD",
    "FAIL_THRESHOLD",
]