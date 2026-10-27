"""Run silver transcript generation locally from recordings in eval input storage."""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

from evals.dataset_generation.silver_transcripts.src.main import run_pipeline
from evals.shared.blob_input import stage_transcription_input_prefix

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download recordings from eval input storage and run silver generation."
    )
    parser.add_argument(
        "--prefix",
        default="transcription/",
        help="Folder/prefix inside the eval input container (default: transcription/)",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("evals/dataset_generation/silver_transcripts/input/azure-local"),
        help="Local download directory",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("evals/dataset_generation/silver_transcripts/output/azure-local"),
        help="Local output directory for drafts and segments",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.expanduser().resolve()
    work_dir = args.work_dir.expanduser().resolve()

    if input_dir.exists():
        shutil.rmtree(input_dir)
    input_dir.mkdir(parents=True, exist_ok=True)

    stage_transcription_input_prefix(destination_dir=input_dir, prefix=args.prefix)
    downloaded = sum(1 for path in input_dir.rglob("*") if path.is_file())
    logger.info("Downloaded %s recording(s) to %s", downloaded, input_dir)
    exit_code = run_pipeline(input_dir=input_dir, work_dir=work_dir, segment_duration_seconds=None)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
