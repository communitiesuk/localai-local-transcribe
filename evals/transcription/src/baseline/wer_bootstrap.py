"""Corpus WER and meeting-block bootstrap helpers for AMI-proxy baseline calibration (AIILG-680).

This module holds the WER calculation logic (per-meeting components, corpus WER, bootstrap,
and artefact payloads). Shared resampling helpers live in ``bootstrap_common.py``. The
runnable entrypoint that writes both the WER and WDER JSON artefacts is
``compute_bootstrap_artefacts.py``.

Meetings are the resampling unit. Aggregate (corpus) WER is total edit errors divided by
total reference words across the selected meetings. The bootstrap estimates uncertainty in
that aggregate for the baseline transcription eval config
(``evals/transcription/configs/larger_cloud_test.yaml``, 10 full audio recordings of the
Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text). It does
not estimate Azure run-to-run randomness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import numpy as np

from evals.transcription.src.baseline.bootstrap_common import (
    bootstrap_summary,
    meeting_block_bootstrap_ratios,
    relative_increase,
)
from evals.transcription.src.constants import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_QUANTILES,
    DEFAULT_RANDOM_SEED,
)


class MeetingWerComponents(NamedTuple):
    """Per-meeting WER edit counts used to build corpus WER.

    reference_words is hits + substitutions + deletions (reference length).
    errors is substitutions + deletions + insertions.
    """

    example_id: str
    hits: int
    substitutions: int
    deletions: int
    insertions: int
    reference_words: int
    errors: int
    meeting_wer: float


def corpus_wer(meetings: list[MeetingWerComponents]) -> float:
    """Return corpus WER as sum(errors) / sum(reference_words) across meetings."""
    total_errors = sum(meeting.errors for meeting in meetings)
    total_reference_words = sum(meeting.reference_words for meeting in meetings)
    return total_errors / total_reference_words


def meeting_components_from_sample(sample: dict) -> MeetingWerComponents:
    """Extract WER edit components from one evaluation sample row."""
    metrics = sample["metrics"]
    hits = int(metrics["hits"])
    substitutions = int(metrics["substitutions"])
    deletions = int(metrics["deletions"])
    insertions = int(metrics["insertions"])
    reference_words = hits + substitutions + deletions
    errors = substitutions + deletions + insertions
    return MeetingWerComponents(
        example_id=str(sample["example_id"]),
        hits=hits,
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        reference_words=reference_words,
        errors=errors,
        meeting_wer=errors / reference_words,
    )


def bootstrap_corpus_wer(
    meetings: list[MeetingWerComponents],
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> np.ndarray:
    """Resample meetings with replacement and return corpus WER for each resample.

    Each bootstrap draw samples ``len(meetings)`` meeting blocks with replacement,
    then recomputes corpus WER on that draw.
    """
    errors = np.array([meeting.errors for meeting in meetings], dtype=np.float64)
    reference_words = np.array([meeting.reference_words for meeting in meetings], dtype=np.float64)
    return meeting_block_bootstrap_ratios(errors, reference_words, n_resamples=n_resamples, random_seed=random_seed)


def build_wer_bootstrap_artefact(
    evaluation_results_path: Path,
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int = DEFAULT_RANDOM_SEED,
    quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
    engine_version: str | None = None,
) -> dict:
    """Build the JSON-serialisable WER bootstrap artefact for one evaluation results file."""
    data = json.loads(evaluation_results_path.read_text(encoding="utf-8"))
    engines: dict = data["engines"]
    resolved_engine = engine_version or next(iter(engines))
    meetings = [meeting_components_from_sample(sample) for sample in engines[resolved_engine]]
    baseline_corpus_wer = corpus_wer(meetings)
    bootstrap_values = bootstrap_corpus_wer(meetings, n_resamples=n_resamples, random_seed=random_seed)
    summary = bootstrap_summary(bootstrap_values, quantiles=quantiles)
    quantile_map: dict[str, float] = summary["quantiles"]  # type: ignore[assignment]
    # Relative increases show how far each upper quantile sits above the observed corpus WER.
    relative_to_baseline = {name: relative_increase(value, baseline_corpus_wer) for name, value in quantile_map.items()}
    return {
        "metric": "corpus_wer",
        "resampling_unit": "meeting",
        "description": (
            "Meeting-block bootstrap of corpus WER on the baseline transcription eval config "
            "(evals/transcription/configs/larger_cloud_test.yaml. 10 full audio recordings of the "
            "Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text). "
            "Estimates uncertainty in the aggregate metric, not provider run-to-run randomness."
        ),
        "source_results_file": evaluation_results_path.name,
        "engine_version": resolved_engine,
        "n_meetings": len(meetings),
        "meetings": [meeting._asdict() for meeting in meetings],
        "baseline_corpus_wer": baseline_corpus_wer,
        "bootstrap": {
            "n_resamples": n_resamples,
            "random_seed": random_seed,
            "quantiles_requested": list(quantiles),
            **summary,
            "relative_increase_vs_baseline_corpus_wer": relative_to_baseline,
        },
    }
