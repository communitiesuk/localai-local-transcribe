"""Configuration for silver transcript generation."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from evals.transcription.src.models import BlobConfig

DEFAULT_CUTOFF_SECONDS = 600.0


class SilverTranscriptConfig(BaseModel):
    """Paths are resolved relative to the YAML configuration file.

    Reuses transcription's BlobConfig: both evals read source recordings from the same
    input container's ``transcription/`` prefix, via the same staging helpers.
    """

    model_config = ConfigDict(extra="forbid")

    input_dir: Path | None = None
    work_dir: Path | None = None
    cutoff_seconds: float = Field(default=DEFAULT_CUTOFF_SECONDS, gt=0, allow_inf_nan=False)
    blob: BlobConfig = Field(default_factory=BlobConfig)
