DIMENSIONS: dict[str, dict] = {
    "accuracy": {
        "label": "Factual Accuracy",
    },
    "numerical_accuracy": {
        "label": "Numeric Fidelity",
    },
    "template_fit": {
        "label": "Template Adherence & Completeness",
    },
    "coverage": {
        "label": "Transcript Factual Completeness",
    },
    "action_clarity": {
        "label": "Actionability",
    },
    "professional_tone": {
        "label": "Tone",
    },
    "readability": {
        "label": "Structure & Readability",
    },
    "auditability": {
        "label": "Citation Quality",
    },
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
