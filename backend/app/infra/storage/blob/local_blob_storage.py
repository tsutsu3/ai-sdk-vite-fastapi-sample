import uuid
from pathlib import Path

from app.core.config import AppConfig
from app.shared.ports import BlobStorage, UploadedFileObject


class LocalBlobStorage(BlobStorage):
    def __init__(self, config: AppConfig) -> None:
        self._base_path = Path(config.local_storage_path).resolve() / "blobs"
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFileObject:
        blob_name = f"{uuid.uuid4()}-{filename}"
        path = self._base_path / blob_name
        path.write_bytes(data)
        return UploadedFileObject(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )

    async def download(self, file_id: str) -> bytes | None:
        path = self._base_path / file_id
        if not path.exists():
            return None
        return path.read_bytes()

    async def get_object_url(self, file_id: str, expires_in_seconds: int | None = None) -> str:
        return f"/api/file/{file_id}/download"
