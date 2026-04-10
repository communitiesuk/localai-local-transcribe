from __future__ import annotations

from dataclasses import dataclass

import dspy

from common.settings import get_settings
from evals.summarisation.src.common.adapter_factory import build_azure_apim_adapter
from evals.summarisation.src.common.config import AppConfig
from evals.summarisation.src.common.dspy_wrapper import DSPyModelAdapterWrapper
from evals.summarisation.src.common.schemas import DialogExample, MetricResult
from evals.summarisation.src.common.signatures import JudgeRatingSignature


@dataclass(frozen=True)
class DialogSummaryMetric:
    """Judge-based metric for evaluating dialogue summaries."""

    name: str
    criterion: str
    pass_threshold: int
    lm: dspy.LM

    def evaluate(
        self,
        *,
        example: DialogExample,
        prediction: dspy.Prediction,
    ) -> MetricResult:
        """Evaluates prediction against example using judge LLM for specific criterion."""
        with dspy.context(lm=self.lm):
            pred = dspy.Predict(JudgeRatingSignature)(
                dialogue=example.dialogue,
                reference_summary=example.reference_summary,
                candidate_summary=prediction.summary,
                criterion=self.criterion,
            )

        rating = int(pred.rating)
        passed = rating >= self.pass_threshold
        return MetricResult(
            score=1.0 if passed else 0.0,
            reason=f"rating={rating} threshold={self.pass_threshold} :: {pred.reason}",
        )


def build_metrics(cfg: AppConfig) -> list[DialogSummaryMetric]:
    """Builds list of judge metrics from configuration."""
    metrics: list[DialogSummaryMetric] = []

    settings = get_settings()
    adapter = build_azure_apim_adapter()
    judge_lm = DSPyModelAdapterWrapper(adapter=adapter, model_name=settings.BEST_LLM_MODEL_NAME)

    for name in cfg.metrics:
        metrics.append(
            DialogSummaryMetric(
                name=f"judge_{name}",
                criterion=name,
                pass_threshold=cfg.judge.pass_threshold,
                lm=judge_lm,
            )
        )

    return metrics
