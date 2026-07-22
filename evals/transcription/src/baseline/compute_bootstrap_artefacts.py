"""Build AMI-proxy WER and WDER bootstrap artefacts for transcription drift thresholds (AIILG-680).

This is the command-line entrypoint. Calculation logic lives in ``wer_bootstrap.py`` and
``wder_bootstrap.py``, with shared resampling helpers in ``bootstrap_common.py``. This script
chooses the input results file, calls both artefact builders, and writes
``evals/transcription/baseline/wer_bootstrap_ami_proxy.json`` and
``evals/transcription/baseline/wder_bootstrap_ami_proxy.json``.

It reads a saved transcription evaluation_results JSON (per-meeting WER and WDER counts) so
relative review and fail bands can be calibrated from uncertainty in the aggregate metrics
for the baseline transcription eval config
(``evals/transcription/configs/larger_cloud_test.yaml``, 10 full audio recordings of the
Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text). Meetings
are the resampling unit. The artefacts estimate uncertainty in the aggregates, not Azure
run-to-run randomness.

Run from the repository root after you have evaluation results under
``evals/transcription/output/``.

    poetry run python -m evals.transcription.src.baseline.compute_bootstrap_artefacts

Optional. Pass an explicit results file path as the first argument.

    poetry run python -m evals.transcription.src.baseline.compute_bootstrap_artefacts \\
        evals/transcription/output/evaluation_results_YYYYMMDD_HHMMSS.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from evals.transcription.src.baseline.wder_bootstrap import build_wder_bootstrap_artefact
from evals.transcription.src.baseline.wer_bootstrap import build_wer_bootstrap_artefact
from evals.transcription.src.constants import (
    WDER_BOOTSTRAP_ARTEFACT_PATH,
    WER_BOOTSTRAP_ARTEFACT_PATH,
    WORKDIR,
)

# Committed artefact directory (distinct from gitignored evals/transcription/output/).
BASELINE_ARTEFACT_DIR = WORKDIR / "baseline"

logger = logging.getLogger(__name__)


def _write_artefact(artefact: dict, artefact_path: Path, baseline_key: str, relative_key: str) -> None:
    """Write one bootstrap artefact and log its baseline and relative-increase summary."""
    artefact_path.write_text(json.dumps(artefact, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %s", artefact_path)
    logger.info("%s=%.6f", baseline_key, artefact[baseline_key])
    bootstrap = artefact["bootstrap"]
    logger.info("bootstrap_mean=%.6f bootstrap_std=%.6f", bootstrap["mean"], bootstrap["std"])
    logger.info("quantiles=%s", bootstrap["quantiles"])
    logger.info("relative_increase_vs_baseline=%s", bootstrap[relative_key])


def main() -> None:
    """Load evaluation results, run WER and WDER bootstraps, and write both AIILG-680 artefacts.

    Uses the newest ``evaluation_results_*.json`` in ``evals/transcription/output/`` unless
    a results file path is given as ``sys.argv[1]``. Writes the committed WER and WDER
    bootstrap artefacts under ``evals/transcription/baseline/``.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    output_dir = WORKDIR / "output"
    if len(sys.argv) > 1:
        results_path = Path(sys.argv[1])
    else:
        results_files = sorted(output_dir.glob("evaluation_results_*.json"))
        if not results_files:
            msg = f"No evaluation_results_*.json found in {output_dir}. Run the eval first, or pass a path."
            raise SystemExit(msg)
        results_path = results_files[-1]

    BASELINE_ARTEFACT_DIR.mkdir(parents=True, exist_ok=True)
    wer_artefact = build_wer_bootstrap_artefact(results_path)
    _write_artefact(
        wer_artefact,
        WER_BOOTSTRAP_ARTEFACT_PATH,
        "baseline_corpus_wer",
        "relative_increase_vs_baseline_corpus_wer",
    )
    wder_artefact = build_wder_bootstrap_artefact(results_path)
    _write_artefact(
        wder_artefact,
        WDER_BOOTSTRAP_ARTEFACT_PATH,
        "baseline_corpus_wder",
        "relative_increase_vs_baseline_corpus_wder",
    )


if __name__ == "__main__":
    main()
