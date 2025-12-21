from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_blob_storage
from app.shared.infra.blob_storage import BlobStorage

router = APIRouter()


@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    storage: BlobStorage = Depends(get_blob_storage),
) -> dict:
    data = await file.read()
    uploaded = await storage.upload(
        data=data,
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename or "upload.bin",
    )
    return {
        "fileId": uploaded.file_id,
        "contentType": uploaded.content_type,
        "size": uploaded.size,
    }
