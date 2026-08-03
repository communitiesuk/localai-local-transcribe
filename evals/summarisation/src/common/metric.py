from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from dataclasses import dataclass

import dspy
from pydantic import BaseModel, ConfigDict, Field

from common.services.template_manager import TemplateManager
from evals.summarisation.src.common.adapter_factory import build_azure_apim_adapter
from evals.summarisation.src.common.config import AppConfig
from evals.summarisation.src.common.schemas import DialogExample, MetricResult
from evals.summarisation.src.constants import CONCURRENCY, normalise_judge_score
from evals.summarisation.src.judge import build_system_prompt, build_user_message, judge_marker_hash

logger = logging.getLogger(__name__)

# The judge dimension that scores citation quality, and so only means anything for a summary path
# that produces citations.
CITATION_DIMENSION = "auditability"


def template_supports_citations(template_name: str | None) -> bool:
    """Whether summaries from ``template_name`` carry ``[n]`` citations into the transcript.

    ``None`` is the basic-minutes fallback used when no template is configured; it has no citation
    step. Any other name is resolved through the production template registry, so an unknown name
    raises rather than quietly answering False — a mistyped template must not silently drop a
    dimension from the run.
    """
    if template_name is None:
        return False
    return TemplateManager.get_template(template_name).citations_required


def judged_dimensions(dimensions: Iterable[str], template_name: str | None) -> list[str]:
    """Filter ``dimensions`` down to those worth judging for ``template_name``.

    Citation quality is dropped for a template that cannot cite. Scored anyway it yields a constant
    rather than a measurement — every such summary earns the same mark for lacking a mechanism it
    was never configured to have — and it drags the run's overall mean down for no reason.
    """
    kept = list(dimensions)
    # Resolved first, and unconditionally, so an unknown template name always raises.
    if template_supports_citations(template_name) or CITATION_DIMENSION not in kept:
        return kept

    logger.info(
        "Skipping %s: template %r does not produce citations, so citation quality is not scored.",
        CITATION_DIMENSION,
        template_name or "<basic minutes>",
    )
    return [d for d in kept if d != CITATION_DIMENSION]


class DimensionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(description="The name of the evaluation dimension (e.g. clarity, correctness).")
    rationale: str = Field(description="The rationale behind the score.")
    score: int = Field(description="The score assigned to this dimension.", ge=0, le=5)


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
    template_name: str | None = None,
    template_content: str | None = None,
    intended_solicitation: str | None = None,
) -> dict:
    """Evaluate multiple dimensions in parallel using separate single-dimension LLM judge calls.

    Every dimension's prompt is byte-identical up to the end of the summary — only the rubric at the
    tail differs — so a provider that caches prompt prefixes can serve most of each call after the
    first. Warming that cache by awaiting one dimension before fanning out the rest is deliberately
    *not* done: it serialises a round trip on every path, and on the paths that judge one summary per
    transcript (the security eval, two dimensions per scenario) it doubles judge wall-clock to save
    two 128-token blocks. The dimensions run concurrently and whichever cache hits, hits.
    """
    semaphore = asyncio.Semaphore(CONCURRENCY)  # Limit concurrency to prevent rate limits

    # Both are the same for every dimension: the system turn carries no rubric, and the marker is
    # drawn per transcript rather than per call, so each dimension's prompt differs only where its
    # rubric does. Built once here rather than per dimension inside the fan-out.
    marker_hash = judge_marker_hash(transcript_text)
    sys_prompt = build_system_prompt(marker_hash=marker_hash, intended_solicitation=intended_solicitation)

    async def evaluate_single_dim(dim: str) -> tuple[str, dict]:
        async with semaphore:
            user_msg = build_user_message(
                summary_id=summary_id,
                transcript_ref=transcript_ref,
                transcript_text=transcript_text,
                summary_text=summary_text,
                target_dimension=dim,
                template_name=template_name,
                template_content=template_content,
                intended_solicitation=intended_solicitation,
                marker_hash=marker_hash,
            )
            res = await call_llm_judge(sys_prompt, user_msg)
            dim_data = res["dimensions"].get(dim)
            if dim_data is None and res["dimensions"]:
                first_key = next(iter(res["dimensions"]))
                dim_data = res["dimensions"][first_key]
            if dim_data is None:
                dim_data = {"score": 1, "rationale": "Missing evaluation data"}
            return dim, dim_data

    tasks = [asyncio.ensure_future(evaluate_single_dim(dim)) for dim in dimensions]
    try:
        results = await asyncio.gather(*tasks)
    finally:
        # A failing dimension makes ``gather`` return while its siblings are still running, holding
        # the semaphore and holding an exception nobody will retrieve. Drain them before the failure
        # leaves this function; on the happy path every task is already done and this is a no-op.
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    merged_dimensions = dict(results)
    return {"dimensions": merged_dimensions}


@dataclass(frozen=True)
class DialogSummaryMetric:
    """Judge-based metric for evaluating dialogue summaries."""

    name: str
    criterion: str
    pass_threshold: int

    def _build_judge_messages(
        self, rubric_dim: str, example: DialogExample, prediction: dspy.Prediction
    ) -> tuple[str, str]:
        marker_hash = judge_marker_hash(example.dialogue)
        sys_prompt = build_system_prompt(marker_hash=marker_hash)
        user_msg = build_user_message(
            summary_id=example.example_id,
            transcript_ref=str(example.example_id),
            transcript_text=example.dialogue,
            summary_text=prediction.summary,
            target_dimension=rubric_dim,
            marker_hash=marker_hash,
        )
        return sys_prompt, user_msg

    def _build_result(self, rubric_dim: str, rubric_evaluation: dict) -> MetricResult:
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
        scaled_score = normalise_judge_score(score)

        return MetricResult(
            score=scaled_score,
            reason=f"rubric_{rubric_dim}_score={score} :: {dim_eval['rationale']}",
        )

    async def evaluate_async(
        self,
        *,
        example: DialogExample,
        prediction: dspy.Prediction,
    ) -> MetricResult:
        """Evaluate prediction using the rubric judge LLM, awaiting the judge call directly.

        Use this from within a running event loop (e.g. the bias pipeline).
        """
        rubric_dim = self.criterion
        sys_prompt, user_msg = self._build_judge_messages(rubric_dim, example, prediction)
        rubric_evaluation = await call_llm_judge(sys_prompt, user_msg)
        return self._build_result(rubric_dim, rubric_evaluation)

    def evaluate(
        self,
        *,
        example: DialogExample,
        prediction: dspy.Prediction,
    ) -> MetricResult:
        """Synchronous wrapper around :meth:`evaluate_async` for non-async callers."""
        return asyncio.run(self.evaluate_async(example=example, prediction=prediction))


def build_metrics(cfg: AppConfig) -> list[DialogSummaryMetric]:
    """Builds list of judge metrics from configuration.

    Dimensions that cannot be judged for the configured summariser template are dropped.
    """
    metrics: list[DialogSummaryMetric] = []

    for name in judged_dimensions(cfg.metrics, cfg.prompts.summarizer_template_name):
        rubric_dim = name

        metrics.append(
            DialogSummaryMetric(
                name=f"rubric_{rubric_dim}",
                criterion=rubric_dim,
                pass_threshold=cfg.judge.pass_threshold,
            )
        )

    return metrics
