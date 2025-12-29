import uuid

from app.shared.ports import BlobStorage, UploadedFileObject


class MemoryBlobStorage(BlobStorage):
    def __init__(self) -> None:
        self._store: dict[str, UploadedFileObject] = {}
        self._bytes: dict[str, bytes] = {}

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFileObject:
        blob_name = f"{uuid.uuid4()}-{filename}"
        uploaded = UploadedFileObject(
            file_id=blob_name,
            content_type=content_type,
            size=len(data),
        )
        self._store[blob_name] = uploaded
        self._bytes[blob_name] = data
        return uploaded

    async def download(self, file_id: str) -> bytes | None:
        return self._bytes.get(file_id)

    async def get_object_url(self, file_id: str, expires_in_seconds: int | None = None) -> str:
        return f"/api/file/{file_id}/download"
