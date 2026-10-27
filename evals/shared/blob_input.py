from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

from evals.shared.blob_io import stage_dataset_prefix
from evals.shared.blob_storage import EvalBlobStorage

DEFAULT_INPUT_PREFIX = "transcription/"
logger = logging.getLogger(__name__)


def stage_transcription_input_prefix(
    *,
    destination_dir: Path,
    prefix: str | None,
    restricted_account_url: str | None = None,
    shared_account_url: str | None = None,
) -> Path:
    selected_prefix = (prefix or DEFAULT_INPUT_PREFIX).strip() or DEFAULT_INPUT_PREFIX
    blob = EvalBlobStorage.from_account_urls(
        restricted_account_url=restricted_account_url,
        shared_account_url=shared_account_url,
    )
    return stage_dataset_prefix(blob, selected_prefix, destination_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download recordings from the evals input container.")
    parser.add_argument("--destination", type=Path, required=True, help="Local destination directory")
    parser.add_argument(
        "--prefix",
        default=DEFAULT_INPUT_PREFIX,
        help="Folder/prefix within the evals input container (default: transcription/)",
    )
    args = parser.parse_args()

    destination = args.destination.expanduser().resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    stage_transcription_input_prefix(destination_dir=destination, prefix=args.prefix)
    downloaded = sum(1 for path in destination.rglob("*") if path.is_file())
    logger.info("Downloaded %s recording(s) from evals input container.", downloaded)


if __name__ == "__main__":
    main()
