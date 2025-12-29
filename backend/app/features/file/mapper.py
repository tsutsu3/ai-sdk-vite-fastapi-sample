from app.features.file.schemas import FileResponse
from app.shared.ports import UploadedFileObject


def file_object_to_response(uploaded: UploadedFileObject) -> FileResponse:
    """Map uploaded file objects to API responses."""
    return FileResponse(
        file_id=uploaded.file_id,
        content_type=uploaded.content_type,
        size=uploaded.size,
    )
