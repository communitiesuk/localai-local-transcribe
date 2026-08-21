from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from evals.shared.blob_storage import EvalBlobStorage


class _FakeService:
    """Minimal stand-in for BlobServiceClient recording uploads."""

    def __init__(self, blobs: dict[tuple[str, str], bytes] | None = None) -> None:
        self._blobs = blobs or {}
        self.uploaded: dict[tuple[str, str], bytes] = {}

    def get_blob_client(self, container: str, blob: str) -> MagicMock:
        client = MagicMock()
        content = self._blobs.get((container, blob), b"")
        stream = MagicMock()
        stream.readall.return_value = content
        client.download_blob.return_value = stream

        def _upload(data: Any, overwrite: bool = False) -> None:  # noqa: ARG001
            self.uploaded[(container, blob)] = data.read()

        client.upload_blob.side_effect = _upload
        return client

def _make_service(**kwargs: Any) -> tuple[_FakeService, Any]:
    service = _FakeService(**kwargs)
    patcher = patch(
        "evals.shared.blob_storage.BlobServiceClient",
        return_value=service,
    )
    return service, patcher


def test_download_blob_writes_file(tmp_path: Path) -> None:
    service, patcher = _make_service(blobs={("input", "summarisation/standard/data.jsonl"): b"line1\nline2\n"})
    dest = tmp_path / "nested" / "data.jsonl"
    with patcher, patch("evals.shared.blob_storage.DefaultAzureCredential"):
        blob = EvalBlobStorage(
            restricted_account_url="https://restricted.blob.core.windows.net",
            shared_account_url="https://shared.blob.core.windows.net",
        )
        result = blob.download_blob("input", "summarisation/standard/data.jsonl", dest)

    assert result == dest
    assert dest.read_bytes() == b"line1\nline2\n"


def test_upload_file(tmp_path: Path) -> None:
    src = tmp_path / "summary.json"
    src.write_bytes(b'{"overall": 4.2}')
    service, patcher = _make_service()
    with patcher, patch("evals.shared.blob_storage.DefaultAzureCredential"):
        blob = EvalBlobStorage(
            restricted_account_url="https://restricted.blob.core.windows.net",
            shared_account_url="https://shared.blob.core.windows.net",
        )
        blob.upload_file("output", "summarisation/standard/run1/summary.json", src)

    assert service.uploaded[("output", "summarisation/standard/run1/summary.json")] == b'{"overall": 4.2}'


def test_from_account_urls_routes_containers_to_separate_accounts(tmp_path: Path) -> None:
    restricted_service = _FakeService(blobs={("input", "summarisation/standard/data.jsonl"): b"line\n"})
    shared_service = _FakeService()
    src = tmp_path / "summary.json"
    src.write_bytes(b"{}")

    with (
        patch(
            "evals.shared.blob_storage.BlobServiceClient",
            side_effect=[restricted_service, shared_service],
        ) as mock_client,
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
    ):
        blob = EvalBlobStorage.from_account_urls(
            restricted_account_url="https://restricted.blob.core.windows.net",
            shared_account_url="https://shared.blob.core.windows.net",
        )
        blob.download_blob("input", "summarisation/standard/data.jsonl", tmp_path / "data.jsonl")
        blob.upload_file("debug", "summarisation/standard/run1/results.jsonl", src)
        blob.upload_file("output", "summarisation/standard/run1/summary.json", src)

    account_urls = [call.kwargs["account_url"] for call in mock_client.call_args_list]
    assert account_urls == [
        "https://restricted.blob.core.windows.net",
        "https://shared.blob.core.windows.net",
    ]
    assert restricted_service.uploaded[("debug", "summarisation/standard/run1/results.jsonl")] == b"{}"
    assert shared_service.uploaded[("output", "summarisation/standard/run1/summary.json")] == b"{}"


def test_from_account_urls_falls_back_to_split_env() -> None:
    with (
        patch.dict(
            "os.environ",
            {
                "AZURE_EVALS_RESTRICTED_STORAGE_ACCOUNT_URL": "https://restricted-env.blob.core.windows.net",
                "AZURE_EVALS_SHARED_STORAGE_ACCOUNT_URL": "https://shared-env.blob.core.windows.net",
            },
            clear=False,
        ),
        patch("evals.shared.blob_storage.BlobServiceClient") as mock_client,
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
    ):
        EvalBlobStorage.from_account_urls()

    account_urls = [call.kwargs["account_url"] for call in mock_client.call_args_list]
    assert account_urls == [
        "https://restricted-env.blob.core.windows.net",
        "https://shared-env.blob.core.windows.net",
    ]


def test_from_account_urls_raises_without_both_account_urls() -> None:
    with (
        patch.dict(
            "os.environ",
            {
                "AZURE_EVALS_RESTRICTED_STORAGE_ACCOUNT_URL": "",
                "AZURE_EVALS_SHARED_STORAGE_ACCOUNT_URL": "",
            },
            clear=False,
        ),
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
        pytest.raises(ValueError, match="restricted_account_url.*shared_account_url"),
    ):
        EvalBlobStorage.from_account_urls()


def test_unknown_container_is_rejected(tmp_path: Path) -> None:
    with (
        patch("evals.shared.blob_storage.BlobServiceClient"),
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
    ):
        blob = EvalBlobStorage(
            restricted_account_url="https://restricted.blob.core.windows.net",
            shared_account_url="https://shared.blob.core.windows.net",
        )

    with pytest.raises(ValueError, match="Unknown eval blob container"):
        blob.upload_file("other", "blob.txt", tmp_path / "blob.txt")
