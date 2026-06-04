DIMENSIONS_LABELS: dict[str, str] = {
    "accuracy": "Factual Accuracy",
    "numerical_accuracy": "Numeric Fidelity",
    "template_fit": "Template Adherence & Completeness",
    "coverage": "Transcript Factual Completeness",
    "action_clarity": "Actionability",
    "professional_tone": "Tone",
    "readability": "Structure & Readability",
    "auditability": "Citation Quality"
}

THRESHOLDS = {
    "critical": 4,
    "review": 2,
    "fail": 1,
}

HALLUCINATION_GATED_DIMENSIONS = {
    "accuracy",
    "numerical_accuracy",
    "action_clarity",
}

CRITICAL_DIMENSIONS = frozenset(HALLUCINATION_GATED_DIMENSIONS)
CRITICAL_THRESHOLD = THRESHOLDS["critical"]
REVIEW_THRESHOLD = THRESHOLDS["review"]
FAIL_THRESHOLD = THRESHOLDS["fail"]
MAX_SCORE_DRIFT = 0.15
MIN_SCORE = 1
MAX_SCORE = 5
MIN_RATIONALE_LENGTH = 20
