from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from common.services.storage_services.azure_blob import AzureBlobStorageService, get_client


@pytest.fixture
def mock_container_client():
    client = AsyncMock()
    client.account_name = "test_account"
    client.container_name = "test_container"
    client.url = "https://local-transcribe-blob.net"
    client.credential = Mock()
    client.credential.account_key = "test_account_key"
    client.get_blob_client = Mock()
    return client


@pytest.fixture
def mock_client_ctx(mocker, mock_container_client):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_container_client)
    ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch(
        "common.services.storage_services.azure_blob.get_client",
        return_value=ctx,
    )
    return ctx


@pytest.fixture
def mock_file_ctx(mocker):
    mock_file = AsyncMock()
    mock_file.read = AsyncMock()
    mock_file.write = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_file)
    ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("common.services.storage_services.azure_blob.aiofiles.open", return_value=ctx)
    return mock_file


@pytest.mark.asyncio
async def test_get_client_raises_if_no_connection_string(mocker):
    dummy_value = "foo"

    mocker.patch("common.services.storage_services.azure_blob.settings.AZURE_BLOB_CONNECTION_STRING", None)
    mocker.patch("common.services.storage_services.azure_blob.settings.AZURE_UPLOADS_CONTAINER_NAME", dummy_value)

    with pytest.raises(ValueError, match="AZURE_BLOB_CONNECTION_STRING must be set"):
        async with get_client():
            pass


@pytest.mark.asyncio
async def test_get_client_raises_if_no_container_name(mocker):
    dummy_value = "bar"

    mocker.patch("common.services.storage_services.azure_blob.settings.AZURE_UPLOADS_CONTAINER_NAME", None)
    mocker.patch("common.services.storage_services.azure_blob.settings.AZURE_BLOB_CONNECTION_STRING", dummy_value)

    with pytest.raises(ValueError, match="AZURE_UPLOADS_CONTAINER_NAME must be set"):
        async with get_client():
            pass


@pytest.mark.asyncio
async def test_upload(
    mock_client_ctx,  # noqa: ARG001
    mock_container_client,
    mock_file_ctx,
):
    key = "test/key.mp3"
    file_content = b"hello world"

    mock_file_ctx.read.return_value = file_content

    await AzureBlobStorageService.upload(key, Path("/file.mp3"))

    mock_container_client.upload_blob.assert_awaited_once_with(name=key, data=file_content)


@pytest.mark.asyncio
async def test_download(
    mock_client_ctx,  # noqa: ARG001
    mock_container_client,
    mock_file_ctx,
):
    blob_key = "/blob.mp3"
    blob_content = b"hello_blob"

    download_stream = AsyncMock()
    download_stream.readall = AsyncMock(return_value=blob_content)

    blob_client = AsyncMock()
    blob_client.download_blob = AsyncMock(return_value=download_stream)
    mock_container_client.get_blob_client.return_value = blob_client

    await AzureBlobStorageService.download(blob_key, Path("/documents/file.mp3"))

    mock_container_client.get_blob_client.assert_called_once_with(blob=blob_key)
    mock_file_ctx.write.assert_awaited_once_with(blob_content)


@pytest.mark.asyncio
async def test_generate_presigned_url_put_object(mocker, mock_client_ctx, mock_container_client):
    sas_tkn = "local_transcribe_token"
    object_key = "audio/bluebeard"
    expiry_period = 3600

    mocker.patch("common.services.storage_services.azure_blob.get_client", return_value=mock_client_ctx)
    mock_generate_sas = mocker.patch(
        "common.services.storage_services.azure_blob.generate_blob_sas", return_value=sas_tkn
    )

    result = await AzureBlobStorageService.generate_presigned_url_put_object(object_key, expiry_seconds=expiry_period)

    assert result == f"{mock_container_client.url}/{object_key}?{sas_tkn}"
    mock_generate_sas.assert_called_once()

    kwargs = mock_generate_sas.call_args.kwargs
    assert kwargs["blob_name"] == object_key
    assert kwargs["container_name"] == mock_container_client.container_name
    permissions = kwargs["permission"]
    assert permissions.read is False
    assert permissions.write is True


@pytest.mark.asyncio
async def test_generate_presigned_url_get_object(mocker, mock_client_ctx, mock_container_client):
    sas_tkn = "local_transcribe_token"
    object_key = "test/key"
    file_name = "the_lost_and"

    mocker.patch("common.services.storage_services.azure_blob.get_client", return_value=mock_client_ctx)
    mock_generate_sas = mocker.patch(
        "common.services.storage_services.azure_blob.generate_blob_sas", return_value=sas_tkn
    )

    result = await AzureBlobStorageService.generate_presigned_url_get_object(
        object_key, filename=file_name, expiry_seconds=3600
    )

    assert result == f"{mock_container_client.url}?{sas_tkn}"
    mock_generate_sas.assert_called_once()

    kwargs = mock_generate_sas.call_args.kwargs
    assert kwargs["blob_name"] == object_key
    assert kwargs["container_name"] == mock_container_client.container_name
    assert kwargs["content_disposition"] == f"attachment; filename={file_name}"
    permissions = kwargs["permission"]
    assert permissions.read is True
    assert permissions.write is False


@pytest.mark.asyncio
async def test_check_object_exists_true(mocker, mock_client_ctx, mock_container_client):
    mocker.patch("common.services.storage_services.azure_blob.get_client", return_value=mock_client_ctx)

    key = "the_wandering"

    blob_client = AsyncMock()
    blob_client.exists = AsyncMock(return_value=True)
    mock_container_client.get_blob_client.return_value = blob_client

    result = await AzureBlobStorageService.check_object_exists(key=key)

    assert result is True
    mock_container_client.get_blob_client.assert_called_once_with(blob=key)


@pytest.mark.asyncio
async def test_check_object_exists_false(mocker, mock_client_ctx, mock_container_client):
    mocker.patch("common.services.storage_services.azure_blob.get_client", return_value=mock_client_ctx)

    key = "the_found"

    blob_client = AsyncMock()
    blob_client.exists = AsyncMock(return_value=False)
    mock_container_client.get_blob_client.return_value = blob_client

    result = await AzureBlobStorageService.check_object_exists(key=key)
    assert result is False
    mock_container_client.get_blob_client.assert_called_once_with(blob=key)


@pytest.mark.asyncio
async def test_delete(mocker, mock_client_ctx, mock_container_client):
    mocker.patch("common.services.storage_services.azure_blob.get_client", return_value=mock_client_ctx)

    key = "borrado"

    blob_client = AsyncMock()
    mock_container_client.get_blob_client.return_value = blob_client

    await AzureBlobStorageService.delete(key)

    mock_container_client.get_blob_client.assert_called_once_with(blob=key)
    blob_client.delete_blob.assert_awaited_once()
