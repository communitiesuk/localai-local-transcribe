"""Build the AMI-proxy WER bootstrap artefact for transcription drift thresholds (AIILG-680).

This is the command-line entrypoint. Calculation logic lives in ``wer_bootstrap.py``. This
script chooses the input results file, calls ``build_wer_bootstrap_artefact``, and writes
``evals/transcription/baseline/wer_bootstrap_ami_proxy.json``.

It reads a saved transcription evaluation_results JSON (per-meeting WER edit counts) so
relative review/fail bands can be calibrated from uncertainty in the aggregate metric.

Run from the repository root after you have evaluation results under
``evals/transcription/output/``.

    poetry run python -m evals.transcription.src.baseline.compute_wer_bootstrap

Optional. Pass an explicit results file path as the first argument.

    poetry run python -m evals.transcription.src.baseline.compute_wer_bootstrap \\
        evals/transcription/output/evaluation_results_YYYYMMDD_HHMMSS.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from evals.transcription.src.baseline.wer_bootstrap import build_wer_bootstrap_artefact
from evals.transcription.src.constants import WORKDIR

# Committed artefact directory (distinct from gitignored evals/transcription/output/).
BASELINE_ARTEFACT_DIR = WORKDIR / "baseline"

logger = logging.getLogger(__name__)


def main() -> None:
    """Load evaluation results, run the WER bootstrap, and write the AIILG-680 artefact.

    Uses the newest ``evaluation_results_*.json`` in ``evals/transcription/output/`` unless
    a results file path is given as ``sys.argv[1]``.
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

    artefact = build_wer_bootstrap_artefact(results_path)
    BASELINE_ARTEFACT_DIR.mkdir(parents=True, exist_ok=True)
    artefact_path = BASELINE_ARTEFACT_DIR / "wer_bootstrap_ami_proxy.json"
    artefact_path.write_text(json.dumps(artefact, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %s", artefact_path)
    logger.info("baseline_corpus_wer=%.6f", artefact["baseline_corpus_wer"])
    bootstrap = artefact["bootstrap"]
    logger.info("bootstrap_mean=%.6f bootstrap_std=%.6f", bootstrap["mean"], bootstrap["std"])
    logger.info("quantiles=%s", bootstrap["quantiles"])
    logger.info(
        "relative_increase_vs_baseline=%s",
        bootstrap["relative_increase_vs_baseline_corpus_wer"],
    )


if __name__ == "__main__":
    main()
