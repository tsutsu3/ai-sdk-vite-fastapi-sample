from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_blob_storage
from app.shared.infra.blob_storage import BlobStorage
from app.features.file.models import FileResponse

router = APIRouter()


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    storage: BlobStorage = Depends(get_blob_storage),
) -> FileResponse:
    data = await file.read()
    uploaded = await storage.upload(
        data=data,
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename or "upload.bin",
    )
    return FileResponse(
        file_id=uploaded.file_id,
        content_type=uploaded.content_type,
        size=uploaded.size,
    )
