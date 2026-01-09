import uuid
from datetime import timedelta

from app.core.config import AppConfig
from app.shared.ports import BlobStorage, UploadedFileObject
from app.shared.time import now_datetime


class GcsBlobStorage(BlobStorage):
    def __init__(self, config: AppConfig) -> None:
        if not config.gcs_bucket:
            raise RuntimeError("GCS bucket is not configured.")
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError("google-cloud-storage is required for GCS blob storage.") from exc

        self._bucket_name = config.gcs_bucket
        self._prefix = config.gcs_prefix.strip("/")
        self._default_url_ttl_seconds = config.blob_object_url_ttl_seconds
        self._client = storage.Client(project=config.gcp_project_id or None)
        self._bucket = self._client.bucket(self._bucket_name)

    def _object_name(self, blob_name: str) -> str:
        if not self._prefix:
            return blob_name
        return f"{self._prefix}/{blob_name}"

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFileObject:
        blob_name = f"{uuid.uuid4()}-{filename}"
        object_name = self._object_name(blob_name)

        def _upload() -> None:
            blob = self._bucket.blob(object_name)
            blob.upload_from_string(data, content_type=content_type)

        import asyncio

        await asyncio.to_thread(_upload)
        return UploadedFileObject(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )

    async def download(self, file_id: str) -> bytes | None:
        object_name = self._object_name(file_id)

        def _download() -> bytes | None:
            blob = self._bucket.blob(object_name)
            if not blob.exists():
                return None
            return blob.download_as_bytes()

        import asyncio

        return await asyncio.to_thread(_download)

    async def get_object_url(self, file_id: str, expires_in_seconds: int | None = None) -> str | None:
        object_name = self._object_name(file_id)
        ttl_seconds = expires_in_seconds or self._default_url_ttl_seconds

        def _signed_url() -> str:
            blob = self._bucket.blob(object_name)
            return blob.generate_signed_url(
                expiration=now_datetime() + timedelta(seconds=ttl_seconds),
                method="GET",
            )

        import asyncio

        return await asyncio.to_thread(_signed_url)
