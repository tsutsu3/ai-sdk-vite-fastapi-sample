import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import AppConfig
from app.core.dependencies import get_app_config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["worker"])


class WorkerJobRunRequest(BaseModel):
    """Payload for triggering a worker job."""

    job_id: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


def _require_worker_auth(
    request: Request,
    app_config: AppConfig = Depends(get_app_config),
) -> None:
    token = (app_config.worker_auth_token or "").strip()
    if not token:
        return
    header_name = app_config.worker_auth_header or "X-Worker-Token"
    provided = request.headers.get(header_name)
    if not provided or provided != token:
        raise HTTPException(status_code=403, detail="Worker authorization failed.")


@router.post("/internal/jobs/run", dependencies=[Depends(_require_worker_auth)])
async def run_job(payload: WorkerJobRunRequest) -> dict[str, str]:
    """Run a worker job (placeholder until job execution is implemented)."""
    logger.info(
        "worker.job.requested job_id=%s payload_keys=%s",
        payload.job_id,
        list(payload.payload.keys()),
    )
    raise HTTPException(status_code=501, detail="Worker job execution is not configured.")
