from pydantic import BaseModel, Field

from common.database.postgres_models import DialogueEntry
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


class EvidenceSpan(BaseModel):
    dialogue_index: int = Field(description="Index of the dialogue entry containing evidence")
    text_snippet: str = Field(description="The relevant text snippet showing the characteristic")
    confidence: float = Field(description="Confidence score for this evidence", ge=0.0, le=1.0)


class CharacteristicDetection(BaseModel):
    axis: ProtectedCharacteristic = Field(description="The protected characteristic axis (e.g., Age, Sex, Race)")
    detected_value: str = Field(description="The detected value for this axis (e.g., 'male', 'senior')")
    evidence_spans: list[EvidenceSpan] = Field(description="Highlighted spans showing evidence")
    overall_confidence: float = Field(description="Overall confidence for this detection", ge=0.0, le=1.0)


class AxisChange(BaseModel):
    axis: ProtectedCharacteristic = Field(
        description="The protected characteristic axis to change (e.g., Age, Sex, Race)"
    )
    original_value: str = Field(description="Original value detected")
    target_value: str = Field(description="Target value to change to")
    instructions: str | None = Field(
        default=None,
        description="Optional specific instructions for this transformation",
    )


class TranscriptInput(BaseModel):
    dialogue_entries: list[DialogueEntry] = Field(description="Original transcript dialogue entries")
    metadata: dict = Field(default_factory=dict, description="Optional metadata from original generation")


class CounterfactualOutput(BaseModel):
    original_transcript: TranscriptInput = Field(description="Original transcript")
    rewritten_transcript: list[DialogueEntry] = Field(description="Rewritten transcript with applied changes")
    axis_change: AxisChange = Field(description="The axis change that was applied")
    model_version: str = Field(description="Model used for rewriting")
    prompt_version: str = Field(description="Prompt version identifier")
    evidence_spans_modified: list[int] = Field(
        description="Indices of dialogue entries that were modified", default_factory=list
    )
