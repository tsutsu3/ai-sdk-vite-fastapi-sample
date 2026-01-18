import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.ai.chains.chat_chain import build_chat_chain
from app.ai.history.factory import build_history_factory
from app.ai.llms.factory import build_chat_model, resolve_chat_model
from app.ai.models import MemoryPolicy
from app.ai.ports import RetrieverBuilder
from app.ai.retrievers.factory import build_retriever_for_provider
from app.ai.runtime import ChatRuntime
from app.core.bootstrap_logging import log_app_configuration
from app.core.config import (
    AppConfig,
    ChatCapabilities,
    ServiceRole,
    Settings,
    StorageCapabilities,
)
from app.core.logging_config import build_logging_config
from app.core.middleware import AuthzContextMiddleware, RequestIdMiddleware
from app.core.request_id import get_current_request_id
from app.core.telemetry import configure_telemetry, instrument_app
from app.features.authz import routes as authz_api
from app.features.authz.service import AuthzService
from app.features.capabilities import routes as capabilities_api
from app.features.chat import routes as chat_api
from app.features.chat.run.errors import RunServiceError
from app.features.chat.run.service import RunService
from app.features.chat.run.streamers import ChatStreamer, LangChainChatStreamer
from app.features.conversations import routes as conversations_api
from app.features.file import routes as file_api
from app.features.health import routes as health_api
from app.features.messages import routes as messages_api
from app.features.retrieval import routes as rag_api
from app.features.retrieval.tools import initialize_tool_specs
from app.features.spa import routes as spa_api
from app.features.title.title_generator import TitleGenerator
from app.features.worker import routes as worker_api
from app.infra.cache.cache_factory import CacheProviderFactory
from app.infra.cache.cached_authz_repository import CachedAuthzRepository
from app.infra.cache.cached_message_repository import CachedMessageRepository
from app.infra.client.cosmos_client import CosmosClientProvider, ensure_cosmos_resources
from app.infra.client.firestore_client import FirestoreClientProvider
from app.infra.fixtures.authz.local_data import (
    PROVISIONING,
    TENANTS,
    USER_IDENTITIES,
    USERS,
)
from app.infra.persistence.factory_selector import create_repository_factory
from app.infra.storage import (
    AzureBlobStorage,
    BlobStorage,
    GcsBlobStorage,
    LocalBlobStorage,
    MemoryBlobStorage,
)

logger = logging.getLogger(__name__)


def _build_blob_storage(app_config: AppConfig, storage_caps: StorageCapabilities) -> BlobStorage:
    """Construct the blob storage backend for the configured storage.

    Args:
        app_config: Application configuration.
        storage_caps: Storage capability configuration.

    Returns:
        BlobStorage: Blob storage backend.
    """
    match storage_caps.blob_backend:
        case "memory":
            return MemoryBlobStorage()
        case "azure":
            return AzureBlobStorage(app_config)
        case "gcp":
            return GcsBlobStorage(app_config)
        case "local":
            return LocalBlobStorage(app_config)
        case _:
            raise RuntimeError("unreachable")


def _build_run_service(
    app_config: AppConfig,
    chat_caps: ChatCapabilities,
    chat_runtime: ChatRuntime | None = None,
    retriever_builder: RetrieverBuilder | None = None,
) -> RunService:
    """Construct the run service for chat execution.

    Args:
        app_config: Application configuration.
        chat_caps: Chat capability configuration.

    Returns:
        RunService: Run service instance.
    """
    streamer: ChatStreamer = LangChainChatStreamer(app_config, chat_caps)
    return RunService(
        streamer,
        TitleGenerator(app_config, streamer),
        chat_runtime=chat_runtime,
        app_config=app_config,
        chat_caps=chat_caps,
        retriever_builder=retriever_builder,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions with a JSON error response.

    Args:
        request: Incoming request.
        exc: Raised exception instance.

    Returns:
        JSONResponse: Error response with HTTP 500.
    """
    logger.exception("Unhandled exception on %s", request.url.path)
    trace_id = getattr(request.state, "request_id", None) or get_current_request_id()
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal Server Error",
                "type": "internal_error",
                "code": "internal_error",
            },
            "detail": "Internal Server Error",
            "trace_id": trace_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.exception("HTTP exception on %s: %s", request.url.path, exc.detail)
    trace_id = getattr(request.state, "request_id", None) or get_current_request_id()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "http_error",
                "code": str(exc.status_code),
            },
            "detail": exc.detail,
            "trace_id": trace_id,
        },
    )


async def run_service_error_handler(request: Request, exc: RunServiceError) -> JSONResponse:
    logger.exception("Run service error on %s: %s", request.url.path, str(exc))
    trace_id = getattr(request.state, "request_id", None) or get_current_request_id()
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": str(exc),
                "type": "run_service_error",
                "code": "run_service_error",
            },
            "detail": str(exc),
            "trace_id": trace_id,
        },
    )


async def _resolve_repositories(
    repository,
    storage_caps: StorageCapabilities,
) -> tuple[object, object, object, object]:
    authz_repo = await repository.authz()
    conversation_repo = await repository.conversations()
    message_repo = await repository.messages()
    job_repo = await repository.jobs()
    return authz_repo, conversation_repo, message_repo, job_repo


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle handler.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Control back to the application runtime.
    """
    logger = logging.getLogger(__name__)

    logger.info("<*> Application startup begin")

    settings = Settings()

    app.state.app_config = settings.to_app_config()
    app.state.storage_capabilities = settings.to_storage_capabilities()
    app.state.chat_capabilities = settings.to_chat_capabilities()
    logger.info(
        "startup.config env=%s db_backend=%s blob_backend=%s auth_provider=%s cache_backend=%s",
        app.state.app_config.app_env,
        app.state.storage_capabilities.db_backend,
        app.state.storage_capabilities.blob_backend,
        app.state.app_config.auth_provider,
        app.state.app_config.cache_backend,
    )
    initialize_tool_specs(app.state.app_config.retrieval_tools_config_path)

    app.state.cosmos_client_provider = None
    app.state.firestore_client_provider = None

    if app.state.storage_capabilities.db_backend == "azure":
        cosmos_client_provider = CosmosClientProvider(app.state.app_config)
        app.state.cosmos_client_provider = cosmos_client_provider

        await ensure_cosmos_resources(
            cosmos_client_provider,
            conversations_container=app.state.app_config.conversations_container,
            messages_container=app.state.app_config.messages_container,
            jobs_container=app.state.app_config.jobs_container,
            users_container=app.state.app_config.users_container,
            tenants_container=app.state.app_config.tenants_container,
            useridentities_container=app.state.app_config.useridentities_container,
            provisioning_container=app.state.app_config.provisioning_container,
        )

    elif app.state.storage_capabilities.db_backend == "gcp":
        firestore_client_provider = FirestoreClientProvider(app.state.app_config)
        app.state.firestore_client_provider = firestore_client_provider

    repository = create_repository_factory(
        app.state.app_config,
        app.state.storage_capabilities,
        cosmos_provider=app.state.cosmos_client_provider,
        firestore_provider=app.state.firestore_client_provider,
        init_tenants=TENANTS,
        init_users=USERS,
        init_user_identities=USER_IDENTITIES,
        init_provisioning=PROVISIONING,
    )

    authz_repo, conversation_repo, message_repo, job_repo = await _resolve_repositories(
        repository,
        app.state.storage_capabilities,
    )

    # Initialize cache providers (separate for authz and messages)
    authz_cache_provider = CacheProviderFactory.create_authz_cache_provider(app.state.app_config)
    messages_cache_provider = CacheProviderFactory.create_messages_cache_provider(
        app.state.app_config
    )

    app.state.authz_cache_provider = authz_cache_provider
    app.state.messages_cache_provider = messages_cache_provider

    # Wrap repositories with cache
    authz_cache_config = CacheProviderFactory.get_authz_config(app.state.app_config)
    messages_cache_config = CacheProviderFactory.get_messages_config(app.state.app_config)

    app.state.authz_repository = CachedAuthzRepository(
        authz_repo,
        cache_provider=authz_cache_provider,
        ttl_seconds=authz_cache_config.ttl_seconds,
    )
    app.state.authz_service = AuthzService(app.state.authz_repository)
    app.state.conversation_repository = conversation_repo
    app.state.message_repository = CachedMessageRepository(
        message_repo,
        cache_provider=messages_cache_provider,
        ttl_seconds=messages_cache_config.ttl_seconds,
    )
    app.state.job_repository = job_repo
    app.state.usage_repository = await repository.usage()

    app.state.blob_storage = _build_blob_storage(
        app.state.app_config, app.state.storage_capabilities
    )
    default_model_id = app.state.app_config.chat_default_model or None
    if not default_model_id:
        candidates = {
            model_id
            for models in app.state.chat_capabilities.providers.values()
            for model_id in models
        }
        if len(candidates) == 1:
            default_model_id = next(iter(candidates))
    if not app.state.chat_capabilities.providers:
        from app.ai.models import ChatModelSpec

        model_spec = ChatModelSpec(provider="fake", model_id="fake-static")
    else:
        model_spec = resolve_chat_model(
            app.state.chat_capabilities,
            None,
            default_model_id=default_model_id,
        )
    llm = build_chat_model(app.state.app_config, model_spec, streaming=True)
    memory_policy = MemoryPolicy()
    history_factory = build_history_factory(
        app.state.message_repository,
        memory_policy,
        write_enabled=False,
    )
    chat_chain = build_chat_chain(llm, history_factory=history_factory)
    app.state.chat_runtime = ChatRuntime(chat_chain, llm, history_factory)
    app.state.run_service = _build_run_service(
        app.state.app_config,
        app.state.chat_capabilities,
        chat_runtime=app.state.chat_runtime,
        retriever_builder=build_retriever_for_provider,
    )

    log_app_configuration(
        app_config=app.state.app_config,
        storage_caps=app.state.storage_capabilities,
        chat_caps=app.state.chat_capabilities,
    )

    try:
        yield
    finally:
        logger.info("<*> Application shutdown begin")

        usage_repo = getattr(app.state, "usage_repository", None)
        flush_usage = getattr(usage_repo, "flush", None) if usage_repo else None
        if callable(flush_usage):
            try:
                await flush_usage()
            except Exception:
                logger.exception("Usage buffer flush failed")

        cosmos_client_provider = app.state.cosmos_client_provider
        if cosmos_client_provider is not None:
            await cosmos_client_provider.close()
            logger.info("<+> Cosmos client closed")

        firestore_client_provider = app.state.firestore_client_provider
        if firestore_client_provider is not None:
            await firestore_client_provider.close()
            logger.info("<+> Firestore client closed")

        authz_cache_provider = app.state.authz_cache_provider
        if authz_cache_provider is not None:
            await authz_cache_provider.close()
            logger.info("<+> Authz cache provider closed")

        messages_cache_provider = app.state.messages_cache_provider
        if messages_cache_provider is not None:
            await messages_cache_provider.close()
            logger.info("<+> Messages cache provider closed")

        logger.info("<*> Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = Settings()
    app_config = settings.to_app_config()
    log_level = app_config.log_level
    log_format = app_config.log_format
    logging.config.dictConfig(
        build_logging_config(log_level=log_level.value, log_format=log_format.value)
    )
    logger = logging.getLogger(__name__)

    configure_telemetry(app_config)

    frontend_dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"

    app = FastAPI(lifespan=lifespan)
    instrument_app(app, app_config)
    if app_config.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_config.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    include_api_routes = app_config.service_role in {ServiceRole.api, ServiceRole.all}
    include_worker_routes = app_config.service_role in {ServiceRole.worker, ServiceRole.all}

    if include_api_routes:
        app.add_middleware(
            AuthzContextMiddleware,
            exclude_paths={"/api/capabilities", "/api/file"},
            exclude_prefixes=("/api/file/",),
        )
    app.add_middleware(RequestIdMiddleware)

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RunServiceError, run_service_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    if include_api_routes and frontend_dist_path.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=frontend_dist_path / "assets"),
            name="assets",
        )
        logger.info("Serving static files from %s", frontend_dist_path / "assets")
    elif include_api_routes:
        logger.warning("Frontend dist directory not found at %s", frontend_dist_path)

    # ===== routers =====
    common_error_responses: dict[int | str, dict[str, Any]] = {
        500: {
            "description": "Unexpected server error.",
            "content": {
                "application/json": {
                    "example": {"error": "Internal Server Error"},
                }
            },
        },
    }

    if include_api_routes:
        app.include_router(authz_api.router, prefix="/api", responses=common_error_responses)
        app.include_router(
            capabilities_api.router, prefix="/api", responses=common_error_responses
        )
        app.include_router(
            conversations_api.router, prefix="/api", responses=common_error_responses
        )
        app.include_router(messages_api.router, prefix="/api", responses=common_error_responses)
        app.include_router(chat_api.router, prefix="/api", responses=common_error_responses)
        app.include_router(file_api.router, prefix="/api", responses=common_error_responses)
        app.include_router(rag_api.router, prefix="/api", responses=common_error_responses)

    if include_worker_routes:
        app.include_router(worker_api.router, responses=common_error_responses)

    app.include_router(health_api.router, responses=common_error_responses)

    if include_api_routes:
        app.include_router(
            spa_api.create_spa_router(frontend_dist_path),
            responses=common_error_responses,
        )

    return app
