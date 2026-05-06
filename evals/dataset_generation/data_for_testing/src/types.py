from typing import Literal, TypeAlias, TypedDict

CharacteristicKey: TypeAlias = tuple[str, str]  # (category, attribute_value)
SpanKey: TypeAlias = tuple[str, str, str]  # (text, category, value)


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
