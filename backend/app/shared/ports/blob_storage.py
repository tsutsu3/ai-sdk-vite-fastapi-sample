from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UploadedFileObject:
    """Metadata for an uploaded file.

    Stored values should match the persisted blob metadata.
    """

    file_id: str
    content_type: str
    size: int


class BlobStorage(Protocol):
    """Interface for blob storage backends.

    This abstraction allows file uploads to be stored in different backends
    (memory, local filesystem, or cloud) without changing API handlers.
    Implementations should be safe for concurrent uploads.
    """

    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFileObject:
        """Store a binary payload and return metadata.

        The filename is preserved in the stored blob identifier.

        Args:
            data: Raw file bytes.
            content_type: MIME type.
            filename: Original filename.

        Returns:
            UploadedFileObject: Stored file metadata.
        """
        raise NotImplementedError

    async def download(self, file_id: str) -> bytes | None:
        """Download a stored blob payload."""
        raise NotImplementedError

    async def get_object_url(
        self, file_id: str, expires_in_seconds: int | None = None
    ) -> str | None:
        """Return a URL for accessing a blob.

        Backends that cannot produce a URL may return None.
        """
        raise NotImplementedError
