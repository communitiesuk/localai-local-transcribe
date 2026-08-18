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

# Common blob-layout conventions for the evals storage accounts.
INPUT_CONTAINER = "input"
RESULTS_CONTAINER = "output"
DEBUG_CONTAINER = "debug"

SENSITIVE_ACCOUNT_ENV_VAR = "AZURE_EVALS_SENSITIVE_STORAGE_ACCOUNT_URL"
RESULTS_ACCOUNT_ENV_VAR = "AZURE_EVALS_RESULTS_STORAGE_ACCOUNT_URL"
LEGACY_ACCOUNT_ENV_VAR = "AZURE_EVALS_STORAGE_ACCOUNT_URL"


def _non_empty(value: str | None) -> str | None:
    return value or None


class EvalBlobStorage:
    def __init__(
        self,
        account_url: str | None = None,
        *,
        sensitive_account_url: str | None = None,
        results_account_url: str | None = None,
        credential: TokenCredential | None = None,
    ) -> None:
        if account_url is not None:
            sensitive_account_url = sensitive_account_url or account_url
            results_account_url = results_account_url or account_url
        if sensitive_account_url is None or results_account_url is None:
            msg = "Set both sensitive_account_url and results_account_url, or set account_url for single-account mode."
            raise ValueError(msg)

        credential = credential or DefaultAzureCredential()
        self._sensitive_service = BlobServiceClient(
            account_url=sensitive_account_url,
            credential=credential,
        )
        self._results_service = BlobServiceClient(
            account_url=results_account_url,
            credential=credential,
        )

    @classmethod
    def from_account_urls(
        cls,
        account_url: str | None = None,
        *,
        sensitive_account_url: str | None = None,
        results_account_url: str | None = None,
        credential: TokenCredential | None = None,
    ) -> EvalBlobStorage:
        account_url = _non_empty(account_url) or _non_empty(os.getenv(LEGACY_ACCOUNT_ENV_VAR))
        sensitive_account_url = _non_empty(sensitive_account_url) or _non_empty(os.getenv(SENSITIVE_ACCOUNT_ENV_VAR))
        results_account_url = _non_empty(results_account_url) or _non_empty(os.getenv(RESULTS_ACCOUNT_ENV_VAR))

        if account_url is None and (sensitive_account_url is None or results_account_url is None):
            msg = (
                "Set blob.sensitive_account_url and blob.results_account_url in the config, "
                f"or {SENSITIVE_ACCOUNT_ENV_VAR} and {RESULTS_ACCOUNT_ENV_VAR}. "
                f"For single-account mode, set blob.account_url or {LEGACY_ACCOUNT_ENV_VAR}."
            )
            raise ValueError(msg)
        return cls(
            account_url,
            sensitive_account_url=sensitive_account_url,
            results_account_url=results_account_url,
            credential=credential,
        )

    @classmethod
    def from_account_url(
        cls,
        account_url: str | None = None,
        credential: TokenCredential | None = None,
    ) -> EvalBlobStorage:
        return cls.from_account_urls(account_url, credential=credential)

    def _service_for(self, container: str) -> BlobServiceClient:
        if container in {INPUT_CONTAINER, DEBUG_CONTAINER}:
            return self._sensitive_service
        if container == RESULTS_CONTAINER:
            return self._results_service
        msg = f"Unknown eval blob container: {container}"
        raise ValueError(msg)

    def download_blob(self, container: str, blob_name: str, dest_path: Path) -> Path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        blob_client = self._service_for(container).get_blob_client(container=container, blob=blob_name)
        with dest_path.open("wb") as f:
            f.write(blob_client.download_blob().readall())
        logger.info("Downloaded %s/%s to %s", container, blob_name, dest_path)
        return dest_path

    def upload_file(self, container: str, blob_name: str, src_path: Path) -> None:
        blob_client = self._service_for(container).get_blob_client(container=container, blob=blob_name)
        with src_path.open("rb") as f:
            blob_client.upload_blob(f, overwrite=True)
        logger.info("Uploaded %s to %s/%s", src_path, container, blob_name)
