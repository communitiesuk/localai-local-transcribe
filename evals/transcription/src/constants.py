"""Shared paths and AMI-proxy drift threshold constants for transcription evals (AIILG-680).

Thresholds are calibrated against the baseline transcription eval config
(``evals/transcription/configs/larger_cloud_test.yaml``. 10 full audio recordings of the
Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text).
"""

from pathlib import Path
from typing import NamedTuple

WORKDIR = Path(__file__).resolve().parent.parent
INPUT_DIR = WORKDIR / "input"
AUDIO_DIR = INPUT_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Committed WER bootstrap artefact used to set relative corpus-WER bands below.
WER_BOOTSTRAP_ARTEFACT_PATH = WORKDIR / "baseline" / "wer_bootstrap_ami_proxy.json"

AGGREGATABLE_METRIC_KEYS = ["wer", "wder", "speaker_count_accuracy", "processing_speed_ratio"]

# Thresholds below are provisional for the baseline transcription eval config only.
DRIFT_THRESHOLDS_ARE_AMI_PROXY_PLACEHOLDERS = True


class WerDriftThresholds(NamedTuple):
    """Relative and absolute gates for corpus WER on the baseline transcription eval config.

    Corpus WER is total edit errors divided by total reference words across meetings.
    Relative increases are (candidate - baseline) / baseline. Higher WER is worse.

    review_relative_increase. Candidate at or above this increase vs baseline goes to review.
    fail_relative_increase. Candidate at or above this increase vs baseline fails.
    absolute_floor. Corpus WER at or above this value always fails, regardless of baseline delta.

    Absolute floors are AMI-proxy disaster lines, not product-readiness bars for real meetings.
    """

    baseline_corpus_wer: float
    review_relative_increase: float
    fail_relative_increase: float
    absolute_floor: float


class SpeakerCountDriftThresholds(NamedTuple):
    """Count-based gates for speaker-count accuracy on the baseline transcription eval config.

    Scores are correct-meeting counts out of n_meetings (for example 7/10), not fine-grained
    proportions, because one meeting moves the rate by 0.10. Higher correct counts are better.
    n_meetings must match num_samples in larger_cloud_test.yaml. See
    require_meeting_count_matches_eval_config.

    review_correct_count. Exactly this many correct meetings triggers review.
    fail_at_or_below_correct_count. This many or fewer correct meetings fails.
    absolute_floor_at_or_below_correct_count. This many or fewer always fails as a floor breach.
    """

    n_meetings: int
    baseline_correct_count: int
    review_correct_count: int
    fail_at_or_below_correct_count: int
    absolute_floor_at_or_below_correct_count: int


class ProcessingSpeedDriftThresholds(NamedTuple):
    """Relative and absolute gates for processing speed ratio (process time / audio duration).

    Higher ratio means slower relative to audio length. Relative increases are
    (candidate - baseline) / baseline.

    absolute_floor. Ratio at or above this value fails as a disaster line.
    hard_floor. Ratio at or above 1.0 means slower than real time and always fails.
    """

    baseline_ratio: float
    review_relative_increase: float
    fail_relative_increase: float
    absolute_floor: float
    hard_floor: float


# TODO(AIILG-680): Replace when the baseline transcription eval config or real audio baseline is recomputed.
# https://mhclgdigital.atlassian.net/browse/AIILG-680
# Baseline and review band follow evals/transcription/baseline/wer_bootstrap_ami_proxy.json
# (corpus WER and bootstrap p95 relative increase ≈ 0.10). Fail +25% sits clearly above
# sampling uncertainty. Absolute floor 0.50 is a loose AMI disaster line only.
WER_DRIFT_THRESHOLDS = WerDriftThresholds(
    baseline_corpus_wer=0.289275,
    review_relative_increase=0.10,
    fail_relative_increase=0.25,
    absolute_floor=0.50,
)

# Speaker-count bands are absolute correct counts out of n_meetings (readable as 7/10, 6/10, ...).
# n_meetings must stay equal to num_samples in evals/transcription/configs/larger_cloud_test.yaml.
# Change the meeting count in the baseline transcription eval config and these counts together, then
# recompute the baseline. Enforcement must call require_meeting_count_matches_eval_config so a
# mismatched run fails fast instead of mis-scoring.
SPEAKER_COUNT_DRIFT_THRESHOLDS = SpeakerCountDriftThresholds(
    n_meetings=10,
    baseline_correct_count=7,
    review_correct_count=6,
    fail_at_or_below_correct_count=5,
    absolute_floor_at_or_below_correct_count=4,
)

# Three-run mean processing_speed_ratio ≈ 0.0441. Relative bands are deliberately loose.
# Three repeats are too thin for a tight cloud-performance estimate.
PROCESSING_SPEED_DRIFT_THRESHOLDS = ProcessingSpeedDriftThresholds(
    baseline_ratio=0.0441,
    review_relative_increase=0.10,
    fail_relative_increase=0.25,
    absolute_floor=0.10,
    hard_floor=1.0,
)
