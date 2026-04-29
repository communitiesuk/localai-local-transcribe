from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

type MetricName = Literal[
    "faithfulness",
    "coverage",
    "conciseness",
    "coherence",
]


def default_criteria() -> list[MetricName]:
    """Returns default list of evaluation criteria."""
    return ["faithfulness", "coverage", "conciseness", "coherence"]


class RunConfig(BaseModel):
    """Configuration for evaluation run parameters."""

    eval_type: Literal["standard", "bias"] = "standard"
    output_dir: str = "runs"
    input_dir: str | None = None
    seed: int = 0
    split: str = "test"
    limit: int | None = None
    prompt_version: str = "dev"
    num_iterations: int | None = None
    dataset_version: str = "unspecified"


class DatasetConfig(BaseModel):
    """Configuration for dataset loading and field mapping."""

    name: str
    config: str | None = None
    dialogue_field: str = "dialogue"
    reference_summary_field: str = "summary"


class JudgeConfig(BaseModel):
    """Configuration for judge evaluation thresholds."""

    pass_threshold: int = 4


class PromptConfig(BaseModel):
    """Configuration for prompt template paths and names."""

    summarizer_template_name: str | None = None
    judge_template_path: str


class HallucinationConfig(BaseModel):
    """Optional addon configuration for evidence-span hallucination detection."""

    enabled: bool = False


class AppConfig(BaseModel):
    """Complete application configuration combining all config sections."""

    run: RunConfig
    dataset: DatasetConfig
    judge: JudgeConfig
    metrics: list[MetricName] = Field(default_factory=default_criteria)
    prompts: PromptConfig
    hallucination: HallucinationConfig = Field(default_factory=HallucinationConfig)


def load_config(path: str | Path) -> AppConfig:
    """Loads and validates application configuration from YAML file."""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AppConfig.model_validate(data)
