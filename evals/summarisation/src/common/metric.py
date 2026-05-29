from __future__ import annotations

import asyncio
from dataclasses import dataclass

import dspy
from pydantic import BaseModel, ConfigDict, Field

from evals.summarisation.prompts.judge import build_system_prompt, build_user_message
from evals.summarisation.src.common.adapter_factory import build_azure_apim_adapter
from evals.summarisation.src.common.config import AppConfig
from evals.summarisation.src.common.schemas import DialogExample, MetricResult


class DimensionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(description="The name of the evaluation dimension (e.g. clarity, correctness).")
    rationale: str = Field(description="The rationale behind the score.")
    score: int = Field(description="The score assigned to this dimension.", ge=1, le=5)


class RubricEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: list[DimensionEvaluation] = Field(description="A list of evaluation dimension scores and rationales.")


async def call_llm_judge(system: str, user: str) -> dict:
    adapter = build_azure_apim_adapter()

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    response = await adapter.structured_chat(messages, RubricEvaluation)

    dimensions_dict = {}
    for item in response.dimensions:
        dimensions_dict[item.name] = {"score": item.score, "rationale": item.rationale}

    return {"dimensions": dimensions_dict}


async def call_llm_judge_parallel(
    *,
    summary_id: str,
    transcript_ref: str,
    transcript_text: str,
    summary_text: str,
    dimensions: list[str],
) -> dict:
    """Evaluate multiple dimensions in parallel using separate single-dimension LLM judge calls."""
    semaphore = asyncio.Semaphore(4)  # Limit concurrency to prevent rate limits

    async def evaluate_single_dim(dim: str) -> tuple[str, dict]:
        async with semaphore:
            sys_prompt = build_system_prompt(dim)
            user_msg = build_user_message(
                summary_id=summary_id,
                transcript_ref=transcript_ref,
                transcript_text=transcript_text,
                summary_text=summary_text,
            )
            res = await call_llm_judge(sys_prompt, user_msg)
            dim_data = res["dimensions"].get(dim)
            if dim_data is None and res["dimensions"]:
                first_key = next(iter(res["dimensions"]))
                dim_data = res["dimensions"][first_key]
            if dim_data is None:
                dim_data = {"score": 1, "rationale": "Missing evaluation data"}
            return dim, dim_data

    tasks = [evaluate_single_dim(d) for d in dimensions]
    results = await asyncio.gather(*tasks)

    merged_dimensions = dict(results)
    return {"dimensions": merged_dimensions}


@dataclass(frozen=True)
class DialogSummaryMetric:
    """Judge-based metric for evaluating dialogue summaries."""

    name: str
    criterion: str
    pass_threshold: int
    lm: dspy.LM | None = None

    def evaluate(
        self,
        *,
        example: DialogExample,
        prediction: dspy.Prediction,
    ) -> MetricResult:
        """Evaluates prediction against example using rubric judge LLM for specific criterion."""
        rubric_dim = self.criterion
        # Map configured metric names to rubric dimension names
        if rubric_dim == "faithfulness":
            rubric_dim = "accuracy"
        elif rubric_dim in ("conciseness", "coherence"):
            rubric_dim = "readability"

        sys_prompt = build_system_prompt(rubric_dim)
        user_msg = build_user_message(
            summary_id=example.example_id,
            transcript_ref=str(example.example_id),
            transcript_text=example.dialogue,
            summary_text=prediction.summary,
        )

        rubric_evaluation = asyncio.run(call_llm_judge(sys_prompt, user_msg))

        dim_eval = rubric_evaluation["dimensions"].get(rubric_dim)
        if dim_eval is None and rubric_evaluation["dimensions"]:
            first_key = next(iter(rubric_evaluation["dimensions"]))
            dim_eval = rubric_evaluation["dimensions"][first_key]

        if dim_eval is None:
            return MetricResult(
                score=0.0,
                reason=f"Dimension '{rubric_dim}' not found in rubric evaluation.",
            )

        score = int(dim_eval["score"])
        scaled_score = (score - 1) / 4.0

        return MetricResult(
            score=scaled_score,
            reason=f"rubric_{rubric_dim}_score={score} :: {dim_eval['rationale']}",
        )


def build_metrics(cfg: AppConfig) -> list[DialogSummaryMetric]:
    """Builds list of judge metrics from configuration."""
    metrics: list[DialogSummaryMetric] = []

    for name in cfg.metrics:
        rubric_dim = name
        if name == "faithfulness":
            rubric_dim = "accuracy"
        elif name in ("conciseness", "coherence"):
            rubric_dim = "readability"

        metrics.append(
            DialogSummaryMetric(
                name=f"rubric_{rubric_dim}",
                criterion=name,
                pass_threshold=cfg.judge.pass_threshold,
            )
        )

    return metrics
