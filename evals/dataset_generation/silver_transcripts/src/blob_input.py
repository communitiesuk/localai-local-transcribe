"""Download selected blob recordings to a local directory for silver transcript generation."""

from __future__ import annotations

import argparse
import asyncio
import shutil
from pathlib import Path

from common.services.storage_services.azure_blob import AzureBlobStorageService

DEFAULT_INPUT_PREFIX = "transcription/"


async def download_recordings(*, destination_dir: Path, prefix: str = DEFAULT_INPUT_PREFIX) -> int:
    selected_prefix = prefix.strip() or DEFAULT_INPUT_PREFIX
    selected = await AzureBlobStorageService.list_blob_names(prefix=selected_prefix)
    if not selected:
        message = f"No blobs found in AZURE_UPLOADS_CONTAINER_NAME for prefix '{selected_prefix}'"
        raise ValueError(message)

    for blob_name in selected:
        destination = destination_dir / blob_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        await AzureBlobStorageService.download(blob_name, destination)
    return len(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download recordings from AZURE_UPLOADS_CONTAINER_NAME.")
    parser.add_argument("--destination", type=Path, required=True, help="Local destination directory")
    parser.add_argument(
        "--prefix",
        default=DEFAULT_INPUT_PREFIX,
        help="Folder/prefix within the uploads container (default: transcription/)",
    )
    args = parser.parse_args()

    destination = args.destination.expanduser().resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    downloaded = asyncio.run(
        download_recordings(
            destination_dir=destination,
            prefix=args.prefix,
        )
    )
    print(f"Downloaded {downloaded} recording(s) from AZURE_UPLOADS_CONTAINER_NAME.")


if __name__ == "__main__":
    main()
