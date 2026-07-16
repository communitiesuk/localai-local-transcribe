"""Shared paths and AMI-proxy drift threshold constants for transcription evals (AIILG-680)."""

from pathlib import Path
from typing import NamedTuple

WORKDIR = Path(__file__).resolve().parent.parent
INPUT_DIR = WORKDIR / "input"
AUDIO_DIR = INPUT_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Committed WER bootstrap artefact used to set relative corpus-WER bands below.
WER_BOOTSTRAP_ARTEFACT_PATH = WORKDIR / "baseline" / "wer_bootstrap_ami_proxy.json"

AGGREGATABLE_METRIC_KEYS = ["wer", "wder", "speaker_count_accuracy", "processing_speed_ratio"]

# Frozen recipe for the AMI-proxy baseline: evals/transcription/configs/larger_cloud_test.yaml
# (10 full meetings, Azure STT). Thresholds below are provisional for that proxy only.
DRIFT_THRESHOLDS_ARE_AMI_PROXY_PLACEHOLDERS = True


class WerDriftThresholds(NamedTuple):
    """Relative and absolute gates for corpus WER on the frozen AMI recipe.

    Corpus WER is total edit errors divided by total reference words across meetings.
    Relative increases are (candidate - baseline) / baseline. Higher WER is worse.

    review_relative_increase: candidate at or above this increase vs baseline goes to review.
    fail_relative_increase: candidate at or above this increase vs baseline fails.
    absolute_floor: corpus WER at or above this value always fails, regardless of baseline delta.

    Absolute floors are AMI-proxy disaster lines, not product-readiness bars for real meetings.
    """

    baseline_corpus_wer: float
    review_relative_increase: float
    fail_relative_increase: float
    absolute_floor: float


class SpeakerCountDriftThresholds(NamedTuple):
    """Count-based gates for speaker-count accuracy on the frozen 10-meeting AMI recipe.

    Scores are correct-meeting counts out of n_meetings (not fine-grained proportions), because
    one meeting moves the rate by 0.10. Higher correct counts are better.

    review_correct_count: exactly this many correct meetings triggers review.
    fail_at_or_below_correct_count: this many or fewer correct meetings fails.
    absolute_floor_at_or_below_correct_count: this many or fewer always fails as a floor breach.
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

    absolute_floor: ratio at or above this value fails as a disaster line.
    hard_floor: ratio at or above 1.0 means slower than real time and always fails.
    """

    baseline_ratio: float
    review_relative_increase: float
    fail_relative_increase: float
    absolute_floor: float
    hard_floor: float


# TODO(AIILG-680): replace when the frozen recipe or real audio baseline is recomputed.
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

# Baseline was 7/10 correct on the frozen recipe. Count thresholds avoid false precision.
SPEAKER_COUNT_DRIFT_THRESHOLDS = SpeakerCountDriftThresholds(
    n_meetings=10,
    baseline_correct_count=7,
    review_correct_count=6,
    fail_at_or_below_correct_count=5,
    absolute_floor_at_or_below_correct_count=4,
)

# Three-run mean processing_speed_ratio ≈ 0.0441. Relative bands are deliberately loose;
# three repeats are too thin for a tight cloud-performance estimate.
PROCESSING_SPEED_DRIFT_THRESHOLDS = ProcessingSpeedDriftThresholds(
    baseline_ratio=0.0441,
    review_relative_increase=0.10,
    fail_relative_increase=0.25,
    absolute_floor=0.10,
    hard_floor=1.0,
)
