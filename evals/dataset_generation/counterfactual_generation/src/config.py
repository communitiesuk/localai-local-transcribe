from pathlib import Path

from pydantic import BaseModel, Field

from evals.dataset_generation.shared_constants import ProtectedCharacteristic


class AxisDefinition(BaseModel):
    axis: ProtectedCharacteristic = Field(description="The protected characteristic axis (e.g., Age, Sex, Race)")
    original_value: str = Field(description="Original value detected in transcript")
    target_value: str = Field(description="Target value to change to")
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
