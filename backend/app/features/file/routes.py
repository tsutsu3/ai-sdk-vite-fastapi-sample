import logging
import mimetypes

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.config import AppConfig
from app.core.dependencies import get_app_config, get_blob_storage
from app.features.file.mapper import file_object_to_response
from app.features.file.schemas import FileResponse
from app.shared.ports import BlobStorage

router = APIRouter()
logger = logging.getLogger(__name__)


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
    app_config: AppConfig = Depends(get_app_config),
) -> FileResponse:
    """Upload a file for later use in chat or tools.

    Stores the file in the configured blob backend and returns metadata.
    """
    if app_config.file_upload_allowed_types:
        content_type = file.content_type or ""
        if content_type not in app_config.file_upload_allowed_types:
            logger.warning(
                "files.upload.rejected reason=unsupported_type content_type=%s", content_type
            )
            raise HTTPException(status_code=415, detail="Unsupported file type")

    data = await file.read()
    if app_config.file_upload_max_bytes and len(data) > app_config.file_upload_max_bytes:
        logger.warning(
            "files.upload.rejected reason=payload_too_large size=%s limit=%s",
            len(data),
            app_config.file_upload_max_bytes,
        )
        raise HTTPException(status_code=413, detail="File too large")
    uploaded = await storage.upload(
        data=data,
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename or "upload.bin",
    )
    logger.info(
        "files.uploaded file_id=%s size=%s content_type=%s",
        uploaded.file_id,
        uploaded.size,
        uploaded.content_type,
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
        logger.warning("files.download.miss file_id=%s", file_id)
        raise HTTPException(status_code=404, detail="File not found")
    content_type, _ = mimetypes.guess_type(file_id)
    logger.info("files.downloaded file_id=%s size=%s", file_id, len(data))
    return Response(content=data, media_type=content_type or "application/octet-stream")
