"""Run silver transcript generation locally from recordings in the uploads bucket."""

from __future__ import annotations

import argparse
import asyncio
import shutil
from pathlib import Path

from evals.dataset_generation.silver_transcripts.src.blob_input import download_recordings
from evals.dataset_generation.silver_transcripts.src.main import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Download recordings from uploads storage and run silver generation.")
    parser.add_argument(
        "--prefix",
        default="transcription/",
        help="Folder/prefix inside AZURE_UPLOADS_CONTAINER_NAME (default: transcription/)",
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

    downloaded = asyncio.run(download_recordings(destination_dir=input_dir, prefix=args.prefix))
    print(f"Downloaded {downloaded} recording(s) to {input_dir}")
    exit_code = run_pipeline(input_dir=input_dir, work_dir=work_dir, segment_duration_seconds=None)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
