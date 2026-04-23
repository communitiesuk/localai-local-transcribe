import datetime
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import ContainerClient

from common.services.storage_services.base import StorageService
from common.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_client() -> AsyncGenerator[ContainerClient, None]:
    if not settings.AZURE_BLOB_CONNECTION_STRING:
        msg = "AZURE_BLOB_CONNECTION_STRING must be set"
        raise ValueError(msg)
    if not settings.AZURE_UPLOADS_CONTAINER_NAME:
        msg = "AZURE_UPLOADS_CONTAINER_NAME must be set"
        raise ValueError(msg)
    async with ContainerClient.from_connection_string(
        settings.AZURE_BLOB_CONNECTION_STRING, settings.AZURE_UPLOADS_CONTAINER_NAME
    ) as container_client:
        yield container_client


class AzureBlobStorageService(StorageService):
    name = "azure_blob"

    @classmethod
    async def upload(cls, key: str, path: Path) -> None:
        async with aiofiles.open(path, "rb") as file, get_client() as container_client:
            file_content = await file.read()
            await container_client.upload_blob(name=key, data=file_content)

    @classmethod
    async def download(cls, key: str, path: Path) -> None:
        async with aiofiles.open(path, "wb") as file, get_client() as container_client:
            blob_client = container_client.get_blob_client(blob=key)
            download_stream = await blob_client.download_blob()
            data = await download_stream.readall()
            await file.write(data)

    @classmethod
    async def generate_presigned_url_put_object(cls, key: str, expiry_seconds: int) -> str:
        async with get_client() as container_client:
            start_time = datetime.datetime.now(datetime.UTC)
            expiry_time = start_time + datetime.timedelta(seconds=expiry_seconds)
            sas_token = generate_blob_sas(
                blob_name=key,
                account_name=container_client.account_name,
                container_name=container_client.container_name,
                account_key=container_client.credential.account_key,
                permission=BlobSasPermissions(write=True),
                expiry=expiry_time,
            )
            return f"{container_client.url}/{key}?{sas_token}"

    @classmethod
    async def generate_presigned_url_get_object(cls, key: str, filename: str, expiry_seconds: int) -> str:
        async with get_client() as container_client:
            start_time = datetime.datetime.now(datetime.UTC)
            expiry_time = start_time + datetime.timedelta(seconds=expiry_seconds)
            sas_token = generate_blob_sas(
                blob_name=key,
                account_name=container_client.account_name,
                container_name=container_client.container_name,
                account_key=container_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time,
                content_disposition=f"attachment; filename={filename}",
            )
            return f"{container_client.url}?{sas_token}"

    @classmethod
    async def check_object_exists(cls, key: str) -> bool:
        async with get_client() as container_client:
            blob_client = container_client.get_blob_client(blob=key)
            exists: bool = await blob_client.exists()
            return exists

    @classmethod
    async def delete(cls, key: str) -> None:
        async with get_client() as container_client:
            blob_client = container_client.get_blob_client(blob=key)
            await blob_client.delete_blob()
