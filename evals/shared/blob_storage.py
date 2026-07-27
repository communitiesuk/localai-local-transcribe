"""Entra ID (DefaultAzureCredential) blob client across the eval containers: input, debug, output."""

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

# Shared blob-layout conventions for the evals storage account.
INPUT_CONTAINER = "input"
RESULTS_CONTAINER = "output"
DEBUG_CONTAINER = "debug"


class EvalBlobStorage:
    def __init__(self, account_url: str, credential: TokenCredential | None = None) -> None:
        self._service = BlobServiceClient(
            account_url=account_url,
            credential=credential or DefaultAzureCredential(),
        )

    @classmethod
    def from_account_url(
        cls,
        account_url: str | None = None,
        credential: TokenCredential | None = None,
    ) -> EvalBlobStorage:
        account_url = account_url or os.getenv("AZURE_EVALS_STORAGE_ACCOUNT_URL")
        if not account_url:
            msg = "Set blob.account_url in the config or AZURE_EVALS_STORAGE_ACCOUNT_URL."
            raise ValueError(msg)
        return cls(account_url, credential=credential)

    def download_blob(self, container: str, blob_name: str, dest_path: Path) -> Path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        blob_client = self._service.get_blob_client(container=container, blob=blob_name)
        with dest_path.open("wb") as f:
            f.write(blob_client.download_blob().readall())
        logger.info("Downloaded %s/%s to %s", container, blob_name, dest_path)
        return dest_path

    def upload_file(self, container: str, blob_name: str, src_path: Path) -> None:
        blob_client = self._service.get_blob_client(container=container, blob=blob_name)
        with src_path.open("rb") as f:
            blob_client.upload_blob(f, overwrite=True)
        logger.info("Uploaded %s to %s/%s", src_path, container, blob_name)
