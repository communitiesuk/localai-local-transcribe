from __future__ import annotations
from typing import Any, NotRequired, TypedDict
from pydantic import BaseModel, Field
from common.database.postgres_models import DialogueEntry


class OriginalTranscript(BaseModel):
    """
    Original transcript with dialogue entries and metadata.
    """

    dialogue_entries: list[DialogueEntry]
    metadata: dict[str, Any]


class AxisChange(BaseModel):
    """
    Describes a counterfactual change along a protected characteristic axis.
    """

    axis: str
    original_value: str
    target_value: str
    instructions: str | None = None


class CounterfactualInput(BaseModel):
    """
    Input data for counterfactual evaluation with original and rewritten transcripts.
    """

    original_transcript: OriginalTranscript
    rewritten_transcript: list[DialogueEntry]
    axis_change: AxisChange
    model_version: str
    prompt_version: str
    evidence_spans_modified: list[int]

    @property
    def original_dialogue_entries(self) -> list[DialogueEntry]:
        return self.original_transcript.dialogue_entries

    @property
    def counterfactual_dialogue_entries(self) -> list[DialogueEntry]:
        return self.rewritten_transcript

    @property
    def protected_characteristic(self) -> str:
        return self.axis_change.axis

    @property
    def axis_of_change(self) -> str:
        return f"{self.axis_change.original_value}_to_{self.axis_change.target_value}"

    @property
    def variant_id(self) -> str:
        return f"{self.protected_characteristic}_{self.axis_of_change}"


class CounterfactualMetricResult(BaseModel):
    """
    Result from a single counterfactual metric evaluation.
    """

    score: float = Field(ge=0.0, le=1.0)
    reason: str


class IterationMetrics(BaseModel):
    """
    Metrics from a single iteration including judge scores and sentiment.
    """

    metrics: dict[str, CounterfactualMetricResult]
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    regard_scores: dict[str, float] | None = None


class MetricStatistics(BaseModel):
    """
    Statistical summary of metric values across iterations.
    """

    mean: float
    std: float
    values: list[float]


class CounterfactualEvalRecord(BaseModel):
    """
    Complete evaluation record for a single counterfactual comparison.
    """

    run_id: str
    timestamp: str
    example_id: str

    transcription_text_original: str
    transcription_text_counterfactual: str

    hypothesis_summaries_original: list[str]
    hypothesis_summaries_counterfactual: list[str]
    hypothesis_model: str
    prompt_version: str

    protected_characteristic: str
    axis_of_change: str

    iterations_original: list[IterationMetrics]
    iterations_counterfactual: list[IterationMetrics]

    metrics_original_stats: dict[str, MetricStatistics]
    metrics_counterfactual_stats: dict[str, MetricStatistics]
    sentiment_delta_stats: MetricStatistics
    regard_delta_stats: MetricStatistics | None = None

    latency_ms: dict[str, int]
    error: dict[str, str] | None = None


class ComparisonMetrics(BaseModel):
    """
    Comparison statistics between original and counterfactual metric values.
    """

    metric_name: str
    original_mean: float
    original_std: float
    counterfactual_mean: float
    counterfactual_std: float
    delta: float
    original_values: list[float]
    counterfactual_values: list[float]


class PlottingRecord(BaseModel):
    """
    Single comparison record formatted for visualization.
    """

    comparison_id: str
    protected_characteristic: str
    axis_of_change: str
    group_a_name: str
    group_b_name: str
    is_supplementary: bool

    metrics: list[ComparisonMetrics]
    sentiment_delta: MetricStatistics
    regard_delta: MetricStatistics | None = None

    num_iterations: int
    hypothesis_model: str
    prompt_version: str


class PlottingOutput(BaseModel):
    """
    Complete plotting output with all comparison records for visualization.
    """

    run_id: str
    timestamp: str
    dataset_version: str
    engine_version: str
    prompt_version: str
    num_iterations: int

    comparisons: list[PlottingRecord]


class CounterfactualRunSummary(BaseModel):
    """
    Aggregated summary of counterfactual evaluation run.
    """

    run_id: str
    timestamp: str
    dataset_version: str
    engine_version: str
    prompt_version: str
    n_comparisons: int

    by_characteristic_and_axis: dict[str, dict[str, Any]]


class MetricData(TypedDict):
    """
    Data structure for a single metric's values and statistics.
    """

    original_values: list[float]
    cf_values: list[float]
    original_mean: float
    cf_mean: float


class AxisComparisonData(TypedDict):
    """
    Aggregated comparison data for a single axis of change.
    """

    num_comparisons: int
    avg_sentiment_delta: float
    avg_regard_delta: NotRequired[float | None]
    avg_judge_score_delta: dict[str, float]


CharacteristicAxisMap = dict[str, dict[str, list[CounterfactualEvalRecord]]]
AggregatedResultsMap = dict[str, dict[str, AxisComparisonData]]
