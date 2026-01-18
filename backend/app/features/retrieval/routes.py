import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi_ai_sdk import AIStream, create_ai_stream_response

from app.ai.llms.factory import build_chat_model, resolve_chat_model
from app.ai.retrievers.factory import build_retriever_for_provider
from app.core.config import AppConfig, ChatCapabilities
from app.core.dependencies import (
    get_app_config,
    get_chat_capabilities,
    get_conversation_repository,
    get_job_repository,
    get_message_repository,
    get_usage_repository,
)
from app.features.conversations.ports import ConversationRepository
from app.features.jobs.models import JobRecord, JobStatus
from app.features.jobs.ports import JobRepository
from app.features.jobs.schemas import JobStatusListResponse, JobStatusResponse
from app.features.messages.ports import MessageRepository
from app.features.retrieval.run.service import build_rag_stream
from app.features.retrieval.run.utils import resolve_conversation_id, uuid4_str
from app.features.retrieval.schemas import RetrievalQueryRequest
from app.features.usage.ports import UsageRepository
from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_user_id,
    get_current_user_info,
)
from app.features.worker.schemas import WorkerJobRunRequest
from app.shared.streaming import stream_with_lifecycle
from app.shared.time import now_datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/rag/query",
    response_class=StreamingResponse,
    tags=["RAG"],
    summary="Stream retrieval results",
    description="Streams retrieval results using AI SDK SSE events.",
    response_description="SSE stream of retrieval results.",
    responses={
        400: {"description": "Invalid request or unknown provider."},
        403: {"description": "Not authorized for the requested data source."},
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "query"],
                                "msg": "Field required",
                                "type": "missing",
                            }
                        ]
                    }
                }
            },
        },
        501: {"description": "Retrieval provider is not configured."},
    },
)
async def query_rag(
    request: Request,
    payload: RetrievalQueryRequest = Body(
        ...,
        description="Retrieval query payload.",
        examples=[
            {
                "query": "Summarize the steps",
                "dataSource": "tool01",
                "provider": "memory",
                "model": "gpt-4o",
                "topK": 5,
            }
        ],
    ),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
    app_config: AppConfig = Depends(get_app_config),
    chat_caps: ChatCapabilities = Depends(get_chat_capabilities),
) -> StreamingResponse:
    """Stream retrieval results using the AI SDK data protocol.

    Returns a Server-Sent Events stream containing retrieval results.
    """
    stream = build_rag_stream(
        payload=payload,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        usage_repo=usage_repo,
        app_config=app_config,
        chat_caps=chat_caps,
        resolver=resolve_chat_model,
        builder=build_chat_model,
        retriever_builder=build_retriever_for_provider,
    )
    guarded_stream = stream_with_lifecycle(
        stream,
        is_disconnected=request.is_disconnected,
        idle_timeout=app_config.stream_idle_timeout_seconds,
        logger=logger,
        stream_name="rag",
    )
    ai_stream = AIStream(guarded_stream)
    response: StreamingResponse = create_ai_stream_response(
        ai_stream,
        headers={
            "x-vercel-ai-protocol": "data",
            "Connection": "keep-alive",
        },
    )
    return response


@router.post(
    "/rag/jobs",
    tags=["RAG"],
    summary="Create longform RAG job",
    description="Creates a longform RAG job and returns the worker payload.",
    responses={
        400: {"description": "Invalid request or unknown provider."},
        403: {"description": "Not authorized for the requested data source."},
        422: {"description": "Validation Error"},
    },
)
async def create_rag_job(
    payload: RetrievalQueryRequest = Body(
        ...,
        description="Retrieval query payload.",
    ),
    job_repo: JobRepository = Depends(get_job_repository),
) -> dict[str, object]:
    """Create a longform RAG job and persist the mapping."""
    user_info = get_current_user_info()
    if user_info is None:
        raise HTTPException(status_code=403, detail="User context is not available.")
    conversation_id = resolve_conversation_id(payload)
    job_id = f"job-{uuid4_str()}"
    job_record = JobRecord(
        job_id=job_id,
        tenant_id=get_current_tenant_id(),
        user_id=get_current_user_id(),
        conversation_id=conversation_id,
        status=JobStatus.queued,
        created_at=now_datetime(),
        updated_at=now_datetime(),
    )
    await job_repo.upsert_job(job_record)
    worker_request = WorkerJobRunRequest(
        job_id=job_id,
        request=payload.model_copy(
            update={"pipeline": "longform", "chat_id": conversation_id}
        ),
        user=user_info,
    )
    return {
        "jobId": job_id,
        "conversationId": conversation_id,
        "workerRequest": worker_request.model_dump(by_alias=True),
    }


@router.get(
    "/rag/jobs/{job_id}",
    tags=["RAG"],
    summary="Get longform RAG job status",
    description="Returns the stored job status and conversation mapping.",
    responses={
        404: {"description": "Job not found."},
        403: {"description": "Not authorized for this job."},
    },
)
async def get_rag_job_status(
    job_id: str,
    job_repo: JobRepository = Depends(get_job_repository),
) -> JobStatusResponse:
    record = await job_repo.get_job(
        tenant_id=get_current_tenant_id(),
        user_id=get_current_user_id(),
        job_id=job_id,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(
        jobId=record.job_id,
        conversationId=record.conversation_id,
        status=record.status,
        createdAt=record.created_at,
        updatedAt=record.updated_at,
    )


@router.get(
    "/rag/jobs",
    tags=["RAG"],
    summary="List longform RAG jobs",
    description="Lists stored longform jobs for the current user.",
)
async def list_rag_jobs(
    limit: int | None = Query(default=None, ge=1, le=100),
    continuation_token: str | None = Query(default=None, alias="continuationToken"),
    job_repo: JobRepository = Depends(get_job_repository),
) -> JobStatusListResponse:
    records, next_token = await job_repo.list_jobs(
        tenant_id=get_current_tenant_id(),
        user_id=get_current_user_id(),
        limit=limit,
        continuation_token=continuation_token,
    )
    items = [
        JobStatusResponse(
            jobId=record.job_id,
            conversationId=record.conversation_id,
            status=record.status,
            createdAt=record.created_at,
            updatedAt=record.updated_at,
        )
        for record in records
    ]
    return JobStatusListResponse(items=items, continuationToken=next_token)
