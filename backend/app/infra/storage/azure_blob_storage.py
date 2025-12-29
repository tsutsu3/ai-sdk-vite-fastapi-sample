import uuid
from datetime import timedelta

from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

from app.core.config import AppConfig
from app.shared.ports import BlobStorage, UploadedFileObject
from app.shared.time import now_datetime


class AzureBlobStorage(BlobStorage):
    def __init__(self, config: AppConfig) -> None:
        if not config.azure_blob_endpoint or not config.azure_blob_api_key:
            raise RuntimeError("Azure Blob settings are not configured.")
        self._account_key = config.azure_blob_api_key
        self._default_url_ttl_seconds = config.blob_object_url_ttl_seconds
        self._service = BlobServiceClient(
            account_url=config.azure_blob_endpoint,
            credential=config.azure_blob_api_key,
        )
        self._container = self._service.get_container_client(config.azure_blob_container)
        self._initialized = False

    async def _ensure_container(self) -> None:
        """Ensure the blob container exists."""
        if self._initialized:
            return
        try:
            await self._container.create_container()
        except Exception:
            pass
        self._initialized = True

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFileObject:
        await self._ensure_container()
        blob_name = f"{uuid.uuid4()}-{filename}"
        await self._container.upload_blob(
            name=blob_name,
            data=data,
            overwrite=False,
            content_settings=ContentSettings(content_type=content_type),
        )
        return UploadedFileObject(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )

    async def download(self, file_id: str) -> bytes | None:
        await self._ensure_container()
        blob_client = self._container.get_blob_client(file_id)
        try:
            downloader = await blob_client.download_blob()
            return await downloader.readall()
        except Exception:
            return None

    async def get_object_url(self, file_id: str, expires_in_seconds: int | None = None) -> str:
        await self._ensure_container()
        ttl_seconds = expires_in_seconds or self._default_url_ttl_seconds
        sas_token = generate_blob_sas(
            account_name=self._service.account_name,
            container_name=self._container.container_name,
            blob_name=file_id,
            account_key=self._account_key,
            permission=BlobSasPermissions(read=True),
            expiry=now_datetime() + timedelta(seconds=ttl_seconds),
        )
        return f"{self._container.url}/{file_id}?{sas_token}"
