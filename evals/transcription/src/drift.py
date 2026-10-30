"""Drift threshold checks for transcription eval metrics (AIILG-680).

Classifies corpus WER, corpus WDER, speaker-count accuracy, and processing speed against the
AMI-proxy constants calibrated on the baseline transcription eval config
(``evals/transcription/configs/larger_cloud_test.yaml``. 10 full audio recordings of the
Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text). Writes a
review artefact when needed, and returns a process exit code.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal, NamedTuple

from evals.transcription.src.baseline.bootstrap_common import relative_increase
from evals.transcription.src.baseline.wder_bootstrap import (
    corpus_wder,
    meeting_wder_components_from_sample,
)
from evals.transcription.src.baseline.wer_bootstrap import (
    corpus_wer,
    meeting_components_from_sample,
)
from evals.transcription.src.constants import (
    PROCESSING_SPEED_DRIFT_THRESHOLDS,
    SPEAKER_COUNT_DRIFT_THRESHOLDS,
    WDER_DRIFT_THRESHOLDS,
    WER_DRIFT_THRESHOLDS,
    ProcessingSpeedDriftThresholds,
    SpeakerCountDriftThresholds,
    WderDriftThresholds,
    WerDriftThresholds,
)
from evals.transcription.src.models import EngineOutput, SampleRow

logger = logging.getLogger(__name__)

DriftOutcome = Literal["pass", "review", "fail", "floor"]

# Higher rank wins when combining per-metric outcomes into one exit decision.
_OUTCOME_RANK: dict[DriftOutcome, int] = {
    "pass": 0,
    "review": 1,
    "fail": 2,
    "floor": 3,
}


class DriftVerdict(NamedTuple):
    """Outcome of one metric drift check.

    metric. Which metric was checked (for example corpus_wer).
    outcome. Pass, review, fail, or floor.
    detail. Plain-language reason for that outcome.
    observed. The numeric value compared against the thresholds.
    """

    metric: str
    outcome: DriftOutcome
    detail: str
    observed: float


def require_meeting_count_matches_eval_config(
    run_meeting_count: int,
    thresholds: SpeakerCountDriftThresholds = SPEAKER_COUNT_DRIFT_THRESHOLDS,
) -> None:
    """Fail fast when a run's meeting count does not match the baseline transcription eval config.

    Speaker-count bands are absolute correct counts out of ``thresholds.n_meetings`` (for example
    7/10). Applying them to a different meeting count would change their meaning silently.
    """
    if run_meeting_count != thresholds.n_meetings:
        msg = (
            "Speaker-count drift check cannot run. Meeting count does not match the "
            "baseline transcription eval config. "
            f"This evaluation run scored {run_meeting_count} meeting(s), but "
            f"SPEAKER_COUNT_DRIFT_THRESHOLDS is defined for {thresholds.n_meetings} meetings "
            f"(7/10, 6/10, and so on. See larger_cloud_test.yaml num_samples). "
            "Using these thresholds on a different meeting count would mis-classify pass, review, "
            "and fail. Either re-run with the baseline transcription eval config (10 meetings), "
            "or update SPEAKER_COUNT_DRIFT_THRESHOLDS and recompute the speaker-count baseline "
            "for the new size."
        )
        raise ValueError(msg)


def classify_wer_drift(
    observed_corpus_wer: float,
    thresholds: WerDriftThresholds = WER_DRIFT_THRESHOLDS,
) -> DriftVerdict:
    """Classify corpus WER against relative bands and the absolute floor."""
    if observed_corpus_wer >= thresholds.absolute_floor:
        return DriftVerdict(
            metric="corpus_wer",
            outcome="floor",
            detail=(
                f"corpus WER {observed_corpus_wer:.6f} is at or above absolute floor "
                f"{thresholds.absolute_floor:.6f}"
            ),
            observed=observed_corpus_wer,
        )
    increase = relative_increase(observed_corpus_wer, thresholds.baseline_corpus_wer)
    if increase >= thresholds.fail_relative_increase:
        return DriftVerdict(
            metric="corpus_wer",
            outcome="fail",
            detail=(
                f"corpus WER {observed_corpus_wer:.6f} is {increase:.2%} above baseline "
                f"{thresholds.baseline_corpus_wer:.6f} (fail at {thresholds.fail_relative_increase:.0%})"
            ),
            observed=observed_corpus_wer,
        )
    if increase >= thresholds.review_relative_increase:
        return DriftVerdict(
            metric="corpus_wer",
            outcome="review",
            detail=(
                f"corpus WER {observed_corpus_wer:.6f} is {increase:.2%} above baseline "
                f"{thresholds.baseline_corpus_wer:.6f} (review at {thresholds.review_relative_increase:.0%})"
            ),
            observed=observed_corpus_wer,
        )
    return DriftVerdict(
        metric="corpus_wer",
        outcome="pass",
        detail=(
            f"corpus WER {observed_corpus_wer:.6f} within relative bands of baseline "
            f"{thresholds.baseline_corpus_wer:.6f}"
        ),
        observed=observed_corpus_wer,
    )


def classify_wder_drift(
    observed_corpus_wder: float,
    thresholds: WderDriftThresholds = WDER_DRIFT_THRESHOLDS,
) -> DriftVerdict:
    """Classify corpus WDER against relative bands and the absolute floor."""
    if observed_corpus_wder >= thresholds.absolute_floor:
        return DriftVerdict(
            metric="corpus_wder",
            outcome="floor",
            detail=(
                f"corpus WDER {observed_corpus_wder:.6f} is at or above absolute floor "
                f"{thresholds.absolute_floor:.6f}"
            ),
            observed=observed_corpus_wder,
        )
    increase = relative_increase(observed_corpus_wder, thresholds.baseline_corpus_wder)
    if increase >= thresholds.fail_relative_increase:
        return DriftVerdict(
            metric="corpus_wder",
            outcome="fail",
            detail=(
                f"corpus WDER {observed_corpus_wder:.6f} is {increase:.2%} above baseline "
                f"{thresholds.baseline_corpus_wder:.6f} (fail at {thresholds.fail_relative_increase:.0%})"
            ),
            observed=observed_corpus_wder,
        )
    if increase >= thresholds.review_relative_increase:
        return DriftVerdict(
            metric="corpus_wder",
            outcome="review",
            detail=(
                f"corpus WDER {observed_corpus_wder:.6f} is {increase:.2%} above baseline "
                f"{thresholds.baseline_corpus_wder:.6f} (review at {thresholds.review_relative_increase:.0%})"
            ),
            observed=observed_corpus_wder,
        )
    return DriftVerdict(
        metric="corpus_wder",
        outcome="pass",
        detail=(
            f"corpus WDER {observed_corpus_wder:.6f} within relative bands of baseline "
            f"{thresholds.baseline_corpus_wder:.6f}"
        ),
        observed=observed_corpus_wder,
    )


def classify_speaker_count_drift(
    correct_count: int,
    run_meeting_count: int,
    thresholds: SpeakerCountDriftThresholds = SPEAKER_COUNT_DRIFT_THRESHOLDS,
) -> DriftVerdict:
    """Classify speaker-count correct meetings against count bands on the baseline transcription eval config."""
    require_meeting_count_matches_eval_config(run_meeting_count, thresholds)
    observed = float(correct_count)
    if correct_count <= thresholds.absolute_floor_at_or_below_correct_count:
        return DriftVerdict(
            metric="speaker_count_accuracy",
            outcome="floor",
            detail=(
                f"{correct_count}/{thresholds.n_meetings} meetings had the correct speaker count "
                f"(absolute floor at or below {thresholds.absolute_floor_at_or_below_correct_count})"
            ),
            observed=observed,
        )
    if correct_count <= thresholds.fail_at_or_below_correct_count:
        return DriftVerdict(
            metric="speaker_count_accuracy",
            outcome="fail",
            detail=(
                f"{correct_count}/{thresholds.n_meetings} meetings had the correct speaker count "
                f"(fail at or below {thresholds.fail_at_or_below_correct_count})"
            ),
            observed=observed,
        )
    if correct_count == thresholds.review_correct_count:
        return DriftVerdict(
            metric="speaker_count_accuracy",
            outcome="review",
            detail=(
                f"{correct_count}/{thresholds.n_meetings} meetings had the correct speaker count "
                f"(review at {thresholds.review_correct_count})"
            ),
            observed=observed,
        )
    return DriftVerdict(
        metric="speaker_count_accuracy",
        outcome="pass",
        detail=(
            f"{correct_count}/{thresholds.n_meetings} meetings had the correct speaker count "
            f"(baseline {thresholds.baseline_correct_count}/{thresholds.n_meetings})"
        ),
        observed=observed,
    )


def classify_processing_speed_drift(
    observed_ratio: float,
    thresholds: ProcessingSpeedDriftThresholds = PROCESSING_SPEED_DRIFT_THRESHOLDS,
) -> DriftVerdict:
    """Classify processing speed ratio against relative bands and absolute floors."""
    if observed_ratio >= thresholds.hard_floor:
        return DriftVerdict(
            metric="processing_speed_ratio",
            outcome="floor",
            detail=(
                f"processing speed ratio {observed_ratio:.6f} is at or above hard floor "
                f"{thresholds.hard_floor:.6f} (slower than real time)"
            ),
            observed=observed_ratio,
        )
    if observed_ratio >= thresholds.absolute_floor:
        return DriftVerdict(
            metric="processing_speed_ratio",
            outcome="floor",
            detail=(
                f"processing speed ratio {observed_ratio:.6f} is at or above absolute floor "
                f"{thresholds.absolute_floor:.6f}"
            ),
            observed=observed_ratio,
        )
    increase = relative_increase(observed_ratio, thresholds.baseline_ratio)
    if increase >= thresholds.fail_relative_increase:
        return DriftVerdict(
            metric="processing_speed_ratio",
            outcome="fail",
            detail=(
                f"processing speed ratio {observed_ratio:.6f} is {increase:.2%} above baseline "
                f"{thresholds.baseline_ratio:.6f} (fail at {thresholds.fail_relative_increase:.0%})"
            ),
            observed=observed_ratio,
        )
    if increase >= thresholds.review_relative_increase:
        return DriftVerdict(
            metric="processing_speed_ratio",
            outcome="review",
            detail=(
                f"processing speed ratio {observed_ratio:.6f} is {increase:.2%} above baseline "
                f"{thresholds.baseline_ratio:.6f} (review at {thresholds.review_relative_increase:.0%})"
            ),
            observed=observed_ratio,
        )
    return DriftVerdict(
        metric="processing_speed_ratio",
        outcome="pass",
        detail=(
            f"processing speed ratio {observed_ratio:.6f} within relative bands of baseline "
            f"{thresholds.baseline_ratio:.6f}"
        ),
        observed=observed_ratio,
    )


def worst_outcome(outcomes: list[DriftOutcome]) -> DriftOutcome:
    """Return the most severe outcome in ``outcomes``."""
    if not outcomes:
        msg = "worst_outcome requires at least one drift outcome"
        raise ValueError(msg)
    return max(outcomes, key=lambda outcome: _OUTCOME_RANK[outcome])


def corpus_wer_from_samples(samples: list[SampleRow]) -> float:
    """Compute corpus WER from per-meeting edit counts
    (hits, substitutions, deletions, and insertions used to form total errors over total reference words).
    """
    meetings = [
        meeting_components_from_sample({"example_id": sample.example_id, "metrics": sample.metrics})
        for sample in samples
    ]
    return corpus_wer(meetings)


def corpus_wder_from_samples(samples: list[SampleRow]) -> float:
    """Compute corpus WDER from per-meeting speaker-error and reference-word counts."""
    meetings = [
        meeting_wder_components_from_sample({"example_id": sample.example_id, "metrics": sample.metrics})
        for sample in samples
    ]
    return corpus_wder(meetings)


def speaker_correct_count(samples: list[SampleRow]) -> int:
    """Count meetings whose speaker_count_accuracy metric is at least 1.0."""
    return sum(1 for sample in samples if sample.metrics["speaker_count_accuracy"] >= 1.0)


def assess_engine_drift(engine_output: EngineOutput) -> list[DriftVerdict]:
    """Run WER, WDER, speaker-count, and speed drift checks for one engine output
    (one speech-to-text (STT) provider's full eval result. A run summary plus one
    sample row per meeting, each holding that meeting's transcripts and metrics).
    """
    samples = engine_output.samples
    return [
        classify_wer_drift(corpus_wer_from_samples(samples)),
        classify_wder_drift(corpus_wder_from_samples(samples)),
        classify_speaker_count_drift(speaker_correct_count(samples), len(samples)),
        classify_processing_speed_drift(engine_output.summary.processing_speed_ratio),
    ]


def apply_drift_thresholds(
    results: list[EngineOutput],
    output_dir: Path,
    timestamp: str,
) -> int:
    """Assess drift for each engine output, write a review file if needed, and return the process exit code.

    The baseline transcription eval config currently runs one speech-to-text (STT) engine (Azure),
    so ``results`` normally has one item. The list form remains so multi-adapter runs can be
    checked the same way.

    Exit 1 for fail or floor on any metric. Exit 0 for pass or review. Any non-pass outcome
    (review, fail, or floor) writes ``drift_review_{timestamp}.json`` under ``output_dir`` with
    the per-metric detail, so a failing run leaves the same inspectable record as a review run.
    """
    all_verdicts: list[dict] = []
    outcomes: list[DriftOutcome] = []
    for engine_output in results:
        engine_verdicts = assess_engine_drift(engine_output)
        for verdict in engine_verdicts:
            logger.info(
                "%s %s: %s (%s)",
                engine_output.summary.engine_version,
                verdict.metric,
                verdict.outcome,
                verdict.detail,
            )
            outcomes.append(verdict.outcome)
            all_verdicts.append(
                {
                    "engine_version": engine_output.summary.engine_version,
                    "metric": verdict.metric,
                    "outcome": verdict.outcome,
                    "detail": verdict.detail,
                    "observed": verdict.observed,
                }
            )

    overall = worst_outcome(outcomes)
    logger.info("Overall drift outcome: %s", overall)

    # Write the per-metric breakdown for any non-pass outcome so review, fail, and floor runs
    # all leave an inspectable record on disk, not only a log line.
    if overall != "pass":
        review_path = output_dir / f"drift_review_{timestamp}.json"
        review_path.write_text(
            json.dumps({"overall_outcome": overall, "checks": all_verdicts}, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("Wrote drift review file to %s", review_path)

    if overall in {"fail", "floor"}:
        return 1
    return 0
