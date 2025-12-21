import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient

from app.core.config import AppConfig


@dataclass(frozen=True)
class UploadedFile:
    file_id: str
    content_type: str
    size: int


class BlobStorage(Protocol):
    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFile:
        raise NotImplementedError


class AzureBlobStorage:
    def __init__(self, config: AppConfig) -> None:
        if not config.azure_blob_endpoint or not config.azure_blob_api_key:
            raise RuntimeError("Azure Blob settings are not configured.")
        self._service = BlobServiceClient(
            account_url=config.azure_blob_endpoint,
            credential=config.azure_blob_api_key,
        )
        self._container = self._service.get_container_client(config.azure_blob_container)
        self._initialized = False

    async def _ensure_container(self) -> None:
        if self._initialized:
            return
        try:
            await self._container.create_container()
        except Exception:
            pass
        self._initialized = True

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFile:
        await self._ensure_container()
        blob_name = f"{uuid.uuid4().hex}-{filename}"
        await self._container.upload_blob(
            name=blob_name,
            data=data,
            overwrite=False,
            content_settings=ContentSettings(content_type=content_type),
        )
        return UploadedFile(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )


class MemoryBlobStorage:
    def __init__(self) -> None:
        self._store: dict[str, UploadedFile] = {}

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFile:
        blob_name = f"{uuid.uuid4().hex}-{filename}"
        uploaded = UploadedFile(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )
        self._store[blob_name] = uploaded
        return uploaded


class LocalBlobStorage:
    def __init__(self, config: AppConfig) -> None:
        self._base_path = Path(config.local_storage_path).resolve() / "blobs"
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFile:
        blob_name = f"{uuid.uuid4().hex}-{filename}"
        path = self._base_path / blob_name
        path.write_bytes(data)
        return UploadedFile(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )
