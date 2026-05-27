from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from evals.summarisation.prompts.judge import (
    CRITICAL_DIMENSIONS,
    CRITICAL_THRESHOLD,
    DIMENSIONS,
    FAIL_THRESHOLD,
    REVIEW_THRESHOLD,
)

# Constants for business logic gates
MAX_SCORE_DRIFT = 0.15
MIN_SCORE = 1
MAX_SCORE = 5
MIN_RATIONALE_LENGTH = 20

_SCHEMA_PATH = Path(__file__).parent / "schema.json"
_SCHEMA: dict = json.loads(_SCHEMA_PATH.read_text())

# Note: Check for jsonschema availability
try:
    from jsonschema import Draft202012Validator

    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False


@dataclass
class ValidationResult:
    valid: bool
    schema_errors: list[str] = field(default_factory=list)
    gate_errors: list[str] = field(default_factory=list)  # hard failures
    gate_warnings: list[str] = field(default_factory=list)  # review flags
    overall_score_drift: float | None = None  # reported vs recomputed

    @property
    def requires_human_review(self) -> bool:
        return bool(self.gate_warnings) or bool(self.gate_errors)

    @property
    def is_deploy_blocked(self) -> bool:
        return bool(self.gate_errors) or not self.valid


def validate_evaluation(data: dict) -> ValidationResult:
    """Full validation of a judge output dict."""
    result = ValidationResult(valid=True)

    # 1. Schema validation
    if _HAS_JSONSCHEMA:
        validator = Draft202012Validator(_SCHEMA)
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        if errors:
            result.valid = False
            result.schema_errors = [
                f"{'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in errors
            ]
            return result
    else:
        _minimal_check(data, result)
        if not result.valid:
            return result

    dims: dict = data.get("dimensions", {})

    # 2. Business-logic gates
    for dim_key, dim_data in dims.items():
        score: int | None = dim_data.get("score")
        if score is None:
            continue

        if score <= FAIL_THRESHOLD:
            result.gate_errors.append(f"{dim_key}: score={score} → FAIL / block deployment")
            result.valid = False
        elif score <= REVIEW_THRESHOLD:
            result.gate_warnings.append(f"{dim_key}: score={score} → review required")

        if dim_key in CRITICAL_DIMENSIONS and score < CRITICAL_THRESHOLD:
            msg = f"{dim_key}: score={score} < {CRITICAL_THRESHOLD} (critical dimension gate) → human review required"
            if msg not in result.gate_warnings and msg not in result.gate_errors:
                result.gate_warnings.append(msg)

    # 3. overall_score drift check
    all_scores = [d["score"] for d in dims.values() if isinstance(d.get("score"), int)]
    if len(all_scores) == len(DIMENSIONS):
        recomputed = round(sum(all_scores) / len(all_scores), 1)
        reported = data.get("overall_score")
        if reported is not None:
            drift = abs(float(reported) - recomputed)
            result.overall_score_drift = drift
            if drift > MAX_SCORE_DRIFT:
                result.gate_warnings.append(
                    f"overall_score mismatch: reported={reported}, recomputed={recomputed} (drift={drift:.2f})"
                )

    return result


def _minimal_check(data: dict, result: ValidationResult) -> None:
    required_top = {"summary_id", "transcript_ref", "evaluated_at", "overall_score", "dimensions"}
    missing_top = required_top - set(data.keys())
    if missing_top:
        result.valid = False
        result.schema_errors.append(f"Missing top-level fields: {sorted(missing_top)}")

    dims = data.get("dimensions", {})
    missing_dims = set(DIMENSIONS) - set(dims.keys())
    if missing_dims:
        result.valid = False
        result.schema_errors.append(f"Missing dimensions: {sorted(missing_dims)}")

    for dim_key, dim_data in dims.items():
        for req in ("score", "rationale", "evidence"):
            if req not in dim_data:
                result.valid = False
                result.schema_errors.append(f"dimensions.{dim_key}: missing '{req}'")

        score = dim_data.get("score")
        if score is not None and not (isinstance(score, int) and MIN_SCORE <= score <= MAX_SCORE):
            result.valid = False
            result.schema_errors.append(f"dimensions.{dim_key}.score={score!r} must be int 1-5")

        rationale = dim_data.get("rationale", "")
        if len(str(rationale)) < MIN_RATIONALE_LENGTH:
            result.valid = False
            result.schema_errors.append(
                f"dimensions.{dim_key}.rationale too short ({len(str(rationale))} chars, min {MIN_RATIONALE_LENGTH})"
            )

        evidence = dim_data.get("evidence")
        if not isinstance(evidence, list) or len(evidence) < 1:
            result.valid = False
            result.schema_errors.append(f"dimensions.{dim_key}.evidence must be a non-empty list")
