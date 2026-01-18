import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_ai_sdk.models import DataEvent, ErrorEvent

from app.ai.llms.factory import build_chat_model, resolve_chat_model
from app.ai.retrievers.factory import build_retriever_for_provider
from app.core.config import AppConfig, ChatCapabilities
from app.core.dependencies import (
    get_app_config,
    get_authz_service,
    get_chat_capabilities,
    get_conversation_repository,
    get_job_repository,
    get_message_repository,
    get_usage_repository,
)
from app.features.authz.request_context import (
    AuthzRequestContext,
    get_current_tenant_id,
    get_current_user_id,
    reset_request_context,
    resolve_request_context,
    set_request_context,
)
from app.features.authz.service import AuthzService
from app.features.conversations.ports import ConversationRepository
from app.features.jobs.models import JobRecord, JobStatus
from app.features.jobs.ports import JobRepository
from app.features.messages.ports import MessageRepository
from app.features.retrieval.run.service import build_rag_stream
from app.features.usage.ports import UsageRepository
from app.features.worker.schemas import WorkerJobRunRequest
from app.shared.time import now_datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["worker"])


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
async def run_job(
    request: Request,
    payload: WorkerJobRunRequest,
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
    job_repo: JobRepository = Depends(get_job_repository),
    app_config: AppConfig = Depends(get_app_config),
    chat_caps: ChatCapabilities = Depends(get_chat_capabilities),
    authz_service: AuthzService = Depends(get_authz_service),
) -> dict[str, str]:
    """Run a worker job for longform retrieval."""
    logger.info("worker.job.requested job_id=%s", payload.job_id)
    tokens = None
    conversation_id = payload.request.chat_id
    record: JobRecord | None = None
    try:
        if payload.user:
            resolution = await authz_service.resolve_access(payload.user)
            context = AuthzRequestContext(
                user=payload.user,
                user_record=resolution.user_record,
                tenant_record=resolution.tenant_record,
                user_identity=resolution.user_identity,
            )
        else:
            context = await resolve_request_context(request)
        tokens = set_request_context(request, context)

        record = JobRecord(
            job_id=payload.job_id,
            tenant_id=get_current_tenant_id(),
            user_id=get_current_user_id(),
            conversation_id=conversation_id,
            status=JobStatus.running,
            created_at=now_datetime(),
            updated_at=now_datetime(),
        )
        await job_repo.upsert_job(record)

        job_request = payload.request.model_copy(update={"pipeline": "longform"})
        stream = build_rag_stream(
            payload=job_request,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            usage_repo=usage_repo,
            app_config=app_config,
            chat_caps=chat_caps,
            resolver=resolve_chat_model,
            builder=build_chat_model,
            retriever_builder=build_retriever_for_provider,
        )
        error_text = None
        async for event in stream:
            if isinstance(event, DataEvent) and event.type == "data-conversation":
                conv_id = event.data.get("convId")
                if isinstance(conv_id, str) and conv_id:
                    conversation_id = conv_id
                    if record:
                        await job_repo.upsert_job(
                            record.model_copy(
                                update={
                                    "conversation_id": conversation_id,
                                    "status": JobStatus.running,
                                    "updated_at": now_datetime(),
                                }
                            )
                        )
            if isinstance(event, ErrorEvent):
                error_text = event.error_text
                break
        if error_text:
            raise HTTPException(status_code=500, detail=error_text)
    except HTTPException:
        if record:
            await job_repo.upsert_job(
                record.model_copy(
                    update={
                        "conversation_id": conversation_id,
                        "status": JobStatus.failed,
                        "updated_at": now_datetime(),
                    }
                )
            )
        raise
    except Exception as exc:
        logger.exception("worker.job.failed job_id=%s error=%s", payload.job_id, str(exc))
        if record:
            await job_repo.upsert_job(
                record.model_copy(
                    update={
                        "conversation_id": conversation_id,
                        "status": JobStatus.failed,
                        "updated_at": now_datetime(),
                    }
                )
            )
        raise HTTPException(status_code=500, detail="Worker job execution failed.") from exc
    finally:
        if tokens:
            reset_request_context(tokens)

    if record:
        await job_repo.upsert_job(
            record.model_copy(
                update={
                    "conversation_id": conversation_id,
                    "status": JobStatus.completed,
                    "updated_at": now_datetime(),
                }
            )
        )
    logger.info("worker.job.completed job_id=%s", payload.job_id)
    return {"jobId": payload.job_id, "status": "completed"}
