from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    CRITICAL_DIMENSIONS,
    CRITICAL_THRESHOLD,
    FAIL_THRESHOLD,
    REVIEW_THRESHOLD,
)


@dataclass
class ValidationResult:
    valid: bool
    schema_errors: list[str] = field(default_factory=list)
    gate_errors: list[str] = field(default_factory=list)  # hard failures
    gate_warnings: list[str] = field(default_factory=list)  # review flags

    @property
    def requires_human_review(self) -> bool:
        return bool(self.gate_warnings) or bool(self.gate_errors)

    @property
    def is_deploy_blocked(self) -> bool:
        return bool(self.gate_errors) or not self.valid


def apply_gates(judge: JudgeOutput) -> ValidationResult:
    result = ValidationResult(valid=True)

    for dim_key, dim in judge.dimensions.items():
        score = dim.score

        if score <= FAIL_THRESHOLD:
            result.valid = False
            result.gate_errors.append(f"{dim_key}: score={score} → FAIL / block deployment")

        elif score <= REVIEW_THRESHOLD:
            result.gate_warnings.append(f"{dim_key}: score={score} → review required")

        if dim_key in CRITICAL_DIMENSIONS and score < CRITICAL_THRESHOLD:
            result.gate_warnings.append(f"{dim_key}: score={score} < {CRITICAL_THRESHOLD} (critical dimension)")

    return result
