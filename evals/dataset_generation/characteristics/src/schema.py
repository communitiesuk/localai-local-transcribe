from pydantic import BaseModel, Field, model_validator

from evals.dataset_generation.shared_constants import ProtectedCharacteristic


class ModelConfig(BaseModel):
    provider: str = Field(default="azure_apim")
    model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.0)


class DatasetConfig(BaseModel):
    input_dir: str = Field(default="evals/dataset_generation/characteristics/input")


class RunConfig(BaseModel):
    output_dir: str = Field(default="evals/dataset_generation/characteristics/output")


class PromptsConfig(BaseModel):
    agent_base_template: str = Field(default="evals/dataset_generation/characteristics/prompts/agent_base.jinja2")


class ChunkingConfig(BaseModel):
    chunk_size_chars: int = Field(default=1000)
    overlap_chars: int = Field(default=400)

    @model_validator(mode="after")
    def overlap_less_than_chunk(self) -> "ChunkingConfig":
        if self.overlap_chars >= self.chunk_size_chars:
            msg = f"overlap_chars ({self.overlap_chars}) must be less than chunk_size_chars ({self.chunk_size_chars})"
            raise ValueError(msg)
        return self


class EvalsConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    run: RunConfig = Field(default_factory=RunConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)


class TextSpan(BaseModel):
    start_index: int | None = Field(None)
    end_index: int | None = Field(None)
    text: str = Field(..., description="The exact substring from the transcript")


class CharacteristicDetection(BaseModel):
    characteristic: ProtectedCharacteristic = Field(...)
    attribute_value: str = Field(..., description="e.g., 'Female', 'Muslim', 'Elderly'")
    evidence_spans: list[TextSpan] = Field(default_factory=list)
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)


class CharacteristicExtractionOutput(BaseModel):
    version: str = Field(default="1.1")
    detected_characteristics: list[CharacteristicDetection]


class ExtractionMetadata(BaseModel):
    model_used: str
    prompt_version: str
    total_chunks_processed: int
    failed_chunks: list[int]


class ProcessedFileResult(BaseModel):
    version: str = Field(default="1.0")
    detected_characteristics: list[CharacteristicDetection]
    metadata: ExtractionMetadata
