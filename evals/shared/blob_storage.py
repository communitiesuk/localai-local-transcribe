"""Entra ID blob clients across the eval containers: input, debug, output."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

if TYPE_CHECKING:
    from pathlib import Path

    from azure.core.credentials import TokenCredential
    from azure.storage.blob import StorageStreamDownloader

logger = logging.getLogger(__name__)

# Shared blob-layout conventions for the evals storage accounts.
INPUT_CONTAINER = "input"
RESULTS_CONTAINER = "output"
DEBUG_CONTAINER = "debug"

RESTRICTED_ACCOUNT_ENV_VAR = "AZURE_EVALS_RESTRICTED_STORAGE_ACCOUNT_URL"
SHARED_ACCOUNT_ENV_VAR = "AZURE_EVALS_SHARED_STORAGE_ACCOUNT_URL"


def _non_empty(value: str | None) -> str | None:
    return value or None


def _safe_destination_path(dest_dir: Path, relative: str, blob_name: str) -> Path:
    base = dest_dir.resolve()
    candidate = (dest_dir / relative).resolve()
    if not candidate.is_relative_to(base) or candidate == base:
        msg = f"Unsafe blob path outside destination: {blob_name}"
        raise ValueError(msg)
    return candidate


def _download_to_path(downloader: StorageStreamDownloader, dest_path: Path) -> None:
    with dest_path.open("wb") as f:
        for chunk in downloader.chunks():
            f.write(chunk)


class EvalBlobStorage:
    def __init__(
        self,
        *,
        restricted_account_url: str,
        shared_account_url: str,
        credential: TokenCredential | None = None,
    ) -> None:
        if not restricted_account_url or not shared_account_url:
            msg = "Set both restricted_account_url and shared_account_url."
            raise ValueError(msg)
        credential = credential or DefaultAzureCredential()
        self._restricted_service = BlobServiceClient(
            account_url=restricted_account_url,
            credential=credential,
        )
        self._shared_service = BlobServiceClient(
            account_url=shared_account_url,
            credential=credential,
        )

    @classmethod
    def from_account_urls(
        cls,
        *,
        restricted_account_url: str | None = None,
        shared_account_url: str | None = None,
        credential: TokenCredential | None = None,
    ) -> EvalBlobStorage:
        restricted_account_url = _non_empty(restricted_account_url) or _non_empty(os.getenv(RESTRICTED_ACCOUNT_ENV_VAR))
        shared_account_url = _non_empty(shared_account_url) or _non_empty(os.getenv(SHARED_ACCOUNT_ENV_VAR))

        if restricted_account_url is None or shared_account_url is None:
            msg = (
                "Set blob.restricted_account_url and blob.shared_account_url in the config, "
                f"or {RESTRICTED_ACCOUNT_ENV_VAR} and {SHARED_ACCOUNT_ENV_VAR}."
            )
            raise ValueError(msg)
        return cls(
            restricted_account_url=restricted_account_url,
            shared_account_url=shared_account_url,
            credential=credential,
        )

    def _service_for(self, container: str) -> BlobServiceClient:
        if container in {INPUT_CONTAINER, DEBUG_CONTAINER}:
            return self._restricted_service
        if container == RESULTS_CONTAINER:
            return self._shared_service
        msg = f"Unknown eval blob container: {container}"
        raise ValueError(msg)

    def download_blob(self, container: str, blob_name: str, dest_path: Path) -> Path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        blob_client = self._service_for(container).get_blob_client(container=container, blob=blob_name)
        _download_to_path(blob_client.download_blob(), dest_path)
        logger.info("Downloaded %s/%s to %s", container, blob_name, dest_path)
        return dest_path

    def download_prefix(self, container: str, prefix: str, dest_dir: Path) -> list[Path]:
        normalized_prefix = prefix.strip("/")
        if not normalized_prefix:
            msg = "prefix must not be empty"
            raise ValueError(msg)

        container_client = self._service_for(container).get_container_client(container)
        downloaded: list[Path] = []
        for blob_properties in container_client.list_blobs(name_starts_with=f"{normalized_prefix}/"):
            blob_name = blob_properties.name
            relative = blob_name.removeprefix(f"{normalized_prefix}/")
            if not relative or relative.endswith("/"):
                continue

            dest_path = _safe_destination_path(dest_dir, relative, blob_name)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            _download_to_path(container_client.download_blob(blob_name), dest_path)
            downloaded.append(dest_path)

        if not downloaded:
            msg = f"No blobs found under {container}/{normalized_prefix}/"
            raise ValueError(msg)
        logger.info("Downloaded %d blobs from %s/%s to %s", len(downloaded), container, normalized_prefix, dest_dir)
        return downloaded

    def upload_file(self, container: str, blob_name: str, src_path: Path) -> None:
        blob_client = self._service_for(container).get_blob_client(container=container, blob=blob_name)
        with src_path.open("rb") as f:
            blob_client.upload_blob(f, overwrite=True)
        logger.info("Uploaded %s to %s/%s", src_path, container, blob_name)
