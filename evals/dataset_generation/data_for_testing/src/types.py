from typing import Literal, TypedDict


class ManualResult(TypedDict):
    manual_text: str
    best_match: str | None
    score: float
    label: Literal["TP", "FN", "FP"]
