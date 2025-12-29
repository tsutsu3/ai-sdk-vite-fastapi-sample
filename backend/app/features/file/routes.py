import mimetypes

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.dependencies import get_blob_storage
from app.features.file.mapper import file_object_to_response
from app.features.file.schemas import FileResponse
from app.shared.ports import BlobStorage

router = APIRouter()


@router.post(
    "/file",
    response_model=FileResponse,
    tags=["Files"],
    summary="Upload file",
    description="Uploads a file to blob storage for later use.",
    response_description="Stored file metadata.",
    status_code=201,
)
async def upload_file(
    file: UploadFile = File(...),
    storage: BlobStorage = Depends(get_blob_storage),
) -> FileResponse:
    """Upload a file for later use in chat or tools.

    Stores the file in the configured blob backend and returns metadata.
    """
    data = await file.read()
    uploaded = await storage.upload(
        data=data,
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename or "upload.bin",
    )
    return file_object_to_response(uploaded)


@router.get(
    "/file/{file_id}/download",
    response_class=Response,
    tags=["Files"],
    summary="Download file",
    description="Downloads a previously uploaded file.",
    response_description="File binary payload.",
    responses={
        200: {"content": {"application/octet-stream": {}}},
        404: {"description": "File not found."},
    },
)
async def download_file(
    file_id: str,
    storage: BlobStorage = Depends(get_blob_storage),
) -> Response:
    data = await storage.download(file_id)
    if data is None:
        raise HTTPException(status_code=404, detail="File not found")
    content_type, _ = mimetypes.guess_type(file_id)
    return Response(content=data, media_type=content_type or "application/octet-stream")
