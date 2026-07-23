"""Corpus WDER and meeting-block bootstrap helpers for AMI-proxy baseline calibration (AIILG-680).

This module holds the WDER calculation logic (per-meeting components, corpus WDER, bootstrap,
and artefact payloads). Shared resampling helpers live in ``bootstrap_common.py``. The
runnable entrypoint that writes both the WER and WDER JSON artefacts is
``compute_bootstrap_artefacts.py``.

Meetings are the resampling unit. Aggregate (corpus) WDER is total speaker-attribution errors
divided by total reference words across the selected meetings. The bootstrap estimates
uncertainty in that aggregate for the baseline transcription eval config
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


class MeetingWderComponents(NamedTuple):
    """Per-meeting WDER counts used to build corpus WDER.

    total_words is the reference word count used as the WDER denominator.
    speaker_errors is the count of correctly transcribed words assigned to the wrong speaker.
    """

    example_id: str
    speaker_errors: int
    total_words: int
    meeting_wder: float


def corpus_wder(meetings: list[MeetingWderComponents]) -> float:
    """Return corpus WDER as sum(speaker_errors) / sum(total_words) across meetings."""
    total_speaker_errors = sum(meeting.speaker_errors for meeting in meetings)
    total_words = sum(meeting.total_words for meeting in meetings)
    return total_speaker_errors / total_words


def meeting_wder_components_from_sample(sample: dict) -> MeetingWderComponents:
    """Extract WDER components from one evaluation sample row."""
    metrics = sample["metrics"]
    speaker_errors = int(metrics["speaker_errors"])
    total_words = int(metrics["total_words"])
    return MeetingWderComponents(
        example_id=str(sample["example_id"]),
        speaker_errors=speaker_errors,
        total_words=total_words,
        meeting_wder=speaker_errors / total_words,
    )


def bootstrap_corpus_wder(
    meetings: list[MeetingWderComponents],
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> np.ndarray:
    """Resample meetings with replacement and return corpus WDER for each resample.

    Each bootstrap draw samples ``len(meetings)`` meeting blocks with replacement,
    then recomputes corpus WDER on that draw.
    """
    speaker_errors = np.array([meeting.speaker_errors for meeting in meetings], dtype=np.float64)
    total_words = np.array([meeting.total_words for meeting in meetings], dtype=np.float64)
    return meeting_block_bootstrap_ratios(speaker_errors, total_words, n_resamples=n_resamples, random_seed=random_seed)


def build_wder_bootstrap_artefact(
    evaluation_results_path: Path,
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int = DEFAULT_RANDOM_SEED,
    quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
    engine_version: str | None = None,
) -> dict:
    """Build the JSON-serialisable WDER bootstrap artefact for one evaluation results file."""
    data = json.loads(evaluation_results_path.read_text(encoding="utf-8"))
    engines: dict = data["engines"]
    resolved_engine = engine_version or next(iter(engines))
    meetings = [meeting_wder_components_from_sample(sample) for sample in engines[resolved_engine]]
    baseline_corpus_wder = corpus_wder(meetings)
    bootstrap_values = bootstrap_corpus_wder(meetings, n_resamples=n_resamples, random_seed=random_seed)
    summary = bootstrap_summary(bootstrap_values, quantiles=quantiles)
    quantile_map: dict[str, float] = summary["quantiles"]  # type: ignore[assignment]
    # Relative increases show how far each upper quantile sits above the observed corpus WDER.
    relative_to_baseline = {
        name: relative_increase(value, baseline_corpus_wder) for name, value in quantile_map.items()
    }
    return {
        "metric": "corpus_wder",
        "resampling_unit": "meeting",
        "description": (
            "Meeting-block bootstrap of corpus WDER on the baseline transcription eval config "
            "(evals/transcription/configs/larger_cloud_test.yaml. 10 full audio recordings of the "
            "Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text). "
            "Estimates uncertainty in the aggregate metric, not provider run-to-run randomness."
        ),
        "source_results_file": evaluation_results_path.name,
        "engine_version": resolved_engine,
        "n_meetings": len(meetings),
        "meetings": [meeting._asdict() for meeting in meetings],
        "baseline_corpus_wder": baseline_corpus_wder,
        "bootstrap": {
            "n_resamples": n_resamples,
            "random_seed": random_seed,
            "quantiles_requested": list(quantiles),
            **summary,
            "relative_increase_vs_baseline_corpus_wder": relative_to_baseline,
        },
    }
