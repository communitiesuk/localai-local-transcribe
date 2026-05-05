from typing import Literal, TypedDict


class ManualEntry(TypedDict):
    text: str
    category: str
    value: str


class SpanContext(TypedDict):
    text: str
    value: str
    category: str


class ManualResult(TypedDict):
    manual_text: str
    best_match: str | None
    score: float
    label: Literal["TP", "FN", "FP"]
