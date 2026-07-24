"""Entra ID (DefaultAzureCredential) blob client across the eval containers: input, debug, output."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from common.settings import get_settings
from evals.summarisation.src.common.config import BlobStorageConfig

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential

logger = logging.getLogger(__name__)


class EvalBlobStorage:
    def __init__(self, account_url: str, credential: TokenCredential | None = None) -> None:
        self._service = BlobServiceClient(
            account_url=account_url,
            credential=credential or DefaultAzureCredential(),
        )

    @classmethod
    def from_config(cls, blob_cfg: BlobStorageConfig, credential: TokenCredential | None = None) -> EvalBlobStorage:
        account_url = blob_cfg.account_url or get_settings().AZURE_EVALS_STORAGE_ACCOUNT_URL
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
