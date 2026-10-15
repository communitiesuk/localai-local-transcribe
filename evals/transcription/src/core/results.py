import json
import logging
from collections import defaultdict
from pathlib import Path

from evals.transcription.src.constants import AGGREGATABLE_METRIC_KEYS
from evals.transcription.src.core.metrics import aggregate_metrics
from evals.transcription.src.models import (
    AggregatedMetricStats,
    EngineOutput,
    SampleRow,
    Summary,
    TimingAccumulator,
)

logger = logging.getLogger(__name__)


def create_summary(
    label: str,
    rows: list[SampleRow],
    _timing: TimingAccumulator,
    run_id: str,
    timestamp: str,
    dataset_version: str,
    dataset_split: str | None,
) -> Summary:
    metrics_list = [row.metrics for row in rows]
    aggregated_dict = aggregate_metrics(metrics_list, AGGREGATABLE_METRIC_KEYS)
    aggregated = {key: AggregatedMetricStats(**stats) for key, stats in aggregated_dict.items()}

    # Gate on the edit counts, not the rate: a filler-only reference has no scorable rate
    # but still contributes real insertions to the corpus score.
    content_rows = [row for row in rows if "content_reference_words" in row.metrics]
    reference_words = sum(row.metrics["content_reference_words"] for row in content_rows)
    errors = sum(
        row.metrics[key]
        for row in content_rows
        for key in ("content_substitutions", "content_deletions", "content_insertions")
    )
    corpus_content_wer = errors / reference_words if reference_words else None

    return Summary(
        run_id=run_id,
        timestamp=timestamp,
        dataset_version=dataset_version,
        engine_version=label,
        split=dataset_split,
        n_examples=len(rows),
        metrics=aggregated,
        corpus_content_wer=corpus_content_wer,
        processing_speed_ratio=_timing.processing_speed_ratio,
    )


def _wer_by_group(samples: list[SampleRow]) -> dict[str, dict]:
    """
    Aggregate mean and corpus WER for groups explicitly supplied by each dataset.
    """
    grouped: dict[str, list[SampleRow]] = defaultdict(list)
    for sample in samples:
        metadata = sample.sample_metadata or {}
        group = metadata.get("group")
        if isinstance(group, str) and group:
            grouped[group].append(sample)

    metrics_by_group: dict[str, dict] = {}
    for group_name, rows in sorted(grouped.items()):
        wer_statistics = aggregate_metrics([row.metrics for row in rows], ["wer"])["wer"]
        substitutions = sum(int(row.metrics["substitutions"]) for row in rows)
        deletions = sum(int(row.metrics["deletions"]) for row in rows)
        insertions = sum(int(row.metrics["insertions"]) for row in rows)
        hits = sum(int(row.metrics["hits"]) for row in rows)
        reference_words = hits + substitutions + deletions
        errors = substitutions + deletions + insertions
        content_rows = [row for row in rows if "content_reference_words" in row.metrics]
        content_statistics = aggregate_metrics([row.metrics for row in content_rows], ["content_wer"])
        content_words = sum(row.metrics["content_reference_words"] for row in content_rows)
        content_errors = sum(
            row.metrics[key]
            for row in content_rows
            for key in ("content_substitutions", "content_deletions", "content_insertions")
        )
        metrics_by_group[group_name] = {
            "n_examples": len(rows),
            "wer": wer_statistics,
            "corpus_wer": errors / reference_words if reference_words else None,
            "reference_words": reference_words,
            "errors": errors,
            **(
                {
                    # Absent when every reference in the group was filler-only.
                    "content_wer": content_statistics.get("content_wer"),
                    "corpus_content_wer": content_errors / content_words if content_words else None,
                    "content_reference_words": content_words,
                    "content_errors": content_errors,
                }
                if content_rows
                else {}
            ),
        }
    return metrics_by_group


def save_results(
    results: list[EngineOutput],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grouped_metrics = {}
    for result in results:
        groups = _wer_by_group(result.samples)
        if groups:
            grouped_metrics[result.summary.engine_version] = groups

    combined = {
        "summaries": [result.summary.model_dump() for result in results],
        "engines": {result.summary.engine_version: [s.model_dump() for s in result.samples] for result in results},
    }

    if grouped_metrics:
        combined["wer_by_group"] = grouped_metrics

    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(combined, file_handle, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", output_path)
