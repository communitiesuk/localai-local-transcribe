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

logger = logging.getLogger(__name__)

# Shared blob-layout conventions for the evals storage accounts.
INPUT_CONTAINER = "input"
RESULTS_CONTAINER = "output"
DEBUG_CONTAINER = "debug"

RESTRICTED_ACCOUNT_ENV_VAR = "AZURE_EVALS_RESTRICTED_STORAGE_ACCOUNT_URL"
SHARED_ACCOUNT_ENV_VAR = "AZURE_EVALS_SHARED_STORAGE_ACCOUNT_URL"


def _non_empty(value: str | None) -> str | None:
    return value or None


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
        with dest_path.open("wb") as f:
            f.write(blob_client.download_blob().readall())
        logger.info("Downloaded %s/%s to %s", container, blob_name, dest_path)
        return dest_path

    def list_blob_names(self, container: str, name_starts_with: str) -> list[str]:
        container_client = self._service_for(container).get_container_client(container)
        return [blob.name for blob in container_client.list_blobs(name_starts_with=name_starts_with)]

    def upload_file(self, container: str, blob_name: str, src_path: Path) -> None:
        blob_client = self._service_for(container).get_blob_client(container=container, blob=blob_name)
        with src_path.open("rb") as f:
            blob_client.upload_blob(f, overwrite=True)
        logger.info("Uploaded %s to %s/%s", src_path, container, blob_name)
