from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError

from common.services.storage_services.s3 import S3StorageService


@pytest.fixture
def mock_s3_client():
    return AsyncMock()


@pytest.fixture
def mock_s3_client_ctx(mocker, mock_s3_client):
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_s3_client)
    ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("common.services.storage_services.s3._create_boto3_s3_client", return_value=ctx)
    return ctx


@pytest.fixture
def mock_file_ctx(mocker):
    mock_file = AsyncMock()
    mock_file.read = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_file)
    ctx.__aexit__ = AsyncMock(return_value=None)
    mocker.patch("common.services.storage_services.s3.aiofiles.open", return_value=ctx)
    return mock_file


@pytest.fixture(autouse=True)
def mock_data_s3_bucket(mocker):
    bucket_name = "test-bucket"
    mocker.patch("common.services.storage_services.s3.settings.DATA_S3_BUCKET", bucket_name)
    mocker.patch.object(S3StorageService, "DATA_S3_BUCKET", bucket_name)
    return bucket_name


@pytest.mark.asyncio
async def test_upload(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_file_ctx,
    mock_data_s3_bucket,
):
    key = "test/key.mp3"
    file_content = b"hello world"

    mock_file_ctx.read.return_value = file_content

    await S3StorageService.upload(key, Path("/file.mp3"))

    mock_s3_client.put_object.assert_awaited_once_with(Bucket=mock_data_s3_bucket, Key=key, Body=file_content)


@pytest.mark.asyncio
async def test_download(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_data_s3_bucket,
):
    key = "/blob.mp3"
    path = Path("/documents/file.mp3")

    await S3StorageService.download(key, path)

    mock_s3_client.download_file.assert_awaited_once_with(mock_data_s3_bucket, key, path)


@pytest.mark.asyncio
async def test_generate_presigned_url_put_object(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_data_s3_bucket,
):
    presigned_url = "https://example.com/put"
    object_key = "audio/bluebeard"
    expiry_period = 3600
    mock_s3_client.generate_presigned_url.return_value = presigned_url

    result = await S3StorageService.generate_presigned_url_put_object(object_key, expiry_seconds=expiry_period)

    assert result == presigned_url
    mock_s3_client.generate_presigned_url.assert_awaited_once_with(
        ClientMethod="put_object",
        Params={
            "Bucket": mock_data_s3_bucket,
            "Key": object_key,
        },
        ExpiresIn=expiry_period,
        HttpMethod="PUT",
    )


@pytest.mark.asyncio
async def test_generate_presigned_url_get_object(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_data_s3_bucket,
):
    presigned_url = "https://example.com/get"
    object_key = "test/key"
    file_name = "the_lost_and"
    mock_s3_client.generate_presigned_url.return_value = presigned_url

    result = await S3StorageService.generate_presigned_url_get_object(
        object_key, filename=file_name, expiry_seconds=3600
    )

    assert result == presigned_url
    mock_s3_client.generate_presigned_url.assert_awaited_once_with(
        ClientMethod="get_object",
        Params={
            "Bucket": mock_data_s3_bucket,
            "Key": object_key,
            "ResponseContentDisposition": (f"attachment; filename=\"{file_name}\"; filename*=UTF-8''{file_name}"),
        },
        ExpiresIn=3600,
    )


@pytest.mark.asyncio
async def test_generate_presigned_url_get_object_with_non_ascii_filename(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
):
    """S3 rejects header values it cannot represent in ISO-8859-1."""
    mock_s3_client.generate_presigned_url.return_value = "https://example.com/get"

    await S3StorageService.generate_presigned_url_get_object(
        "test/key", filename="Alpha \u2014 Adoption & Model.mp3", expiry_seconds=3600
    )

    disposition = mock_s3_client.generate_presigned_url.call_args.kwargs["Params"]["ResponseContentDisposition"]
    disposition.encode("iso-8859-1")
    assert disposition == (
        'attachment; filename="Alpha Adoption & Model.mp3"; '
        "filename*=UTF-8''Alpha%20%E2%80%94%20Adoption%20%26%20Model.mp3"
    )


@pytest.mark.asyncio
async def test_check_object_exists_true(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_data_s3_bucket,
):
    key = "the_wandering"

    result = await S3StorageService.check_object_exists(key=key)

    assert result is True
    mock_s3_client.head_object.assert_awaited_once_with(Bucket=mock_data_s3_bucket, Key=key)


@pytest.mark.asyncio
async def test_check_object_exists_false(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_data_s3_bucket,
):
    key = "the_found"
    mock_s3_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadObject",
    )

    result = await S3StorageService.check_object_exists(key=key)

    assert result is False
    mock_s3_client.head_object.assert_awaited_once_with(Bucket=mock_data_s3_bucket, Key=key)


@pytest.mark.asyncio
async def test_delete(
    mock_s3_client_ctx,  # noqa: ARG001
    mock_s3_client,
    mock_data_s3_bucket,
):
    key = "borrado"

    await S3StorageService.delete(key)

    mock_s3_client.delete_object.assert_awaited_once_with(Bucket=mock_data_s3_bucket, Key=key)
