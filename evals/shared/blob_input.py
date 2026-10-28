"""Stage transcription inputs from the restricted eval storage account."""

import argparse
import logging
from pathlib import Path

from evals.shared.blob_io import stage_dataset_prefix
from evals.shared.blob_storage import EvalBlobStorage

DEFAULT_INPUT_PREFIX = "transcription/"
logger = logging.getLogger(__name__)


def stage_transcription_input_prefix(
    *,
    destination_dir: Path,
    prefix: str | None = None,
    restricted_account_url: str | None = None,
) -> Path:
    """Download a transcription input prefix to a local directory."""
    selected_prefix = (prefix or DEFAULT_INPUT_PREFIX).strip() or DEFAULT_INPUT_PREFIX
    blob = EvalBlobStorage.from_account_urls(restricted_account_url=restricted_account_url, require_shared=False)
    return stage_dataset_prefix(blob, selected_prefix, destination_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download recordings from the evals input container.")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--prefix", default=DEFAULT_INPUT_PREFIX)
    args = parser.parse_args()

    destination = args.destination.expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        msg = f"Destination must be empty: {destination}"
        raise ValueError(msg)
    destination.mkdir(parents=True, exist_ok=True)
    stage_transcription_input_prefix(destination_dir=destination, prefix=args.prefix)
    logger.info("Downloaded %d files to %s", sum(path.is_file() for path in destination.rglob("*")), destination)


if __name__ == "__main__":
    main()
