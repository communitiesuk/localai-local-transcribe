from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from evals.shared.blob_storage import EvalBlobStorage


class _FakeService:
    """Minimal stand-in for BlobServiceClient recording uploads."""

    def __init__(self, blobs: dict[tuple[str, str], bytes] | None = None) -> None:
        self._blobs = blobs or {}
        self.uploaded: dict[tuple[str, str], bytes] = {}

    def get_blob_client(self, container: str, blob: str):
        client = MagicMock()
        content = self._blobs.get((container, blob), b"")
        stream = MagicMock()
        stream.readall.return_value = content
        client.download_blob.return_value = stream

        def _upload(data, overwrite=False):  # noqa: ARG001
            self.uploaded[(container, blob)] = data.read()

        client.upload_blob.side_effect = _upload
        return client


def _make_service(**kwargs):
    service = _FakeService(**kwargs)
    patcher = patch(
        "evals.shared.blob_storage.BlobServiceClient",
        return_value=service,
    )
    return service, patcher


def test_download_blob_writes_file(tmp_path):
    service, patcher = _make_service(blobs={("input", "summarisation/standard/data.jsonl"): b"line1\nline2\n"})
    dest = tmp_path / "nested" / "data.jsonl"
    with patcher, patch("evals.shared.blob_storage.DefaultAzureCredential"):
        blob = EvalBlobStorage("https://acct.blob.core.windows.net")
        result = blob.download_blob("input", "summarisation/standard/data.jsonl", dest)

    assert result == dest
    assert dest.read_bytes() == b"line1\nline2\n"


def test_upload_file(tmp_path):
    src = tmp_path / "summary.json"
    src.write_bytes(b'{"overall": 4.2}')
    service, patcher = _make_service()
    with patcher, patch("evals.shared.blob_storage.DefaultAzureCredential"):
        blob = EvalBlobStorage("https://acct.blob.core.windows.net")
        blob.upload_file("output", "summarisation/standard/run1/summary.json", src)

    assert service.uploaded[("output", "summarisation/standard/run1/summary.json")] == b'{"overall": 4.2}'


def test_from_account_url_uses_given_url():
    with (
        patch("evals.shared.blob_storage.BlobServiceClient") as mock_client,
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
    ):
        EvalBlobStorage.from_account_url("https://cfg.blob.core.windows.net")

    _, kwargs = mock_client.call_args
    assert kwargs["account_url"] == "https://cfg.blob.core.windows.net"


def test_from_account_url_falls_back_to_env():
    with (
        patch.dict("os.environ", {"AZURE_EVALS_STORAGE_ACCOUNT_URL": "https://env.blob.core.windows.net"}, clear=False),
        patch("evals.shared.blob_storage.BlobServiceClient") as mock_client,
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
    ):
        EvalBlobStorage.from_account_url(None)

    _, kwargs = mock_client.call_args
    assert kwargs["account_url"] == "https://env.blob.core.windows.net"


def test_from_account_url_raises_without_account_url():
    with (
        patch.dict("os.environ", {"AZURE_EVALS_STORAGE_ACCOUNT_URL": ""}, clear=False),
        patch("evals.shared.blob_storage.DefaultAzureCredential"),
        pytest.raises(ValueError, match="account_url"),
    ):
        EvalBlobStorage.from_account_url(None)
