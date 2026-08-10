from pathlib import Path

from pydantic import BaseModel, Field

from evals.dataset_generation.shared_constants import ProtectedCharacteristic


class AxisDefinition(BaseModel):
    axis: ProtectedCharacteristic = Field(description="The protected characteristic axis (e.g., Age, Sex, Race)")
    original_value: str = Field(description="Original value detected in transcript")
    target_value: str = Field(description="Target value to change to")
    detection_attribute_value: str | None = Field(
        default=None,
        description=(
            "The exact attribute_value string from the characteristic detection output that this "
            "axis change was locked against. Detection reads the transcript in chunks and can "
            "report several values for the same axis, so this names which of those records should "
            "supply the evidence spans that guide the rewrite. When left unset, the most confident "
            "record for the axis is used."
        ),
    )
    instructions: str | None = Field(
        default=None,
        description="Optional specific instructions for this transformation",
    )


class CounterfactualConfig(BaseModel):
    transcript_path: str = Field(description="Path to original transcript JSON file")
    characteristic_detection_path: str | None = Field(
        default=None, description="Optional path to characteristic detection JSON file (if not using auto-detection)"
    )
    axes: list[AxisDefinition] = Field(description="List of axis changes to apply", default_factory=list, min_length=1)

    def get_transcript_path(self, base_dir: Path) -> Path:
        path = Path(self.transcript_path)
        return path if path.is_absolute() else base_dir / path

    def get_characteristic_detection_path(self, base_dir: Path) -> Path | None:
        if self.characteristic_detection_path is None:
            return None
        path = Path(self.characteristic_detection_path)
        return path if path.is_absolute() else base_dir / path
