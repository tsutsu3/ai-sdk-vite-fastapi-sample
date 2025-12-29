import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.bootstrap_logging import log_app_configuration
from app.core.config import AppConfig, ChatCapabilities, Settings, StorageCapabilities
from app.core.logging_config import build_logging_config
from app.core.telemetry import configure_telemetry, instrument_app
from app.features.authz import routes as authz_api
from app.features.authz.service import AuthzService
from app.features.chat import routes as chat_api
from app.features.chat.capabilities import routes as capabilities_api
from app.features.chat.streamers import (
    AzureOpenAIStreamer,
    ChatStreamer,
    MemoryStreamer,
    MultiChatStreamer,
    OllamaStreamer,
)
from app.features.conversations import routes as conversations_api
from app.features.file import routes as file_api
from app.features.health import routes as health_api
from app.features.messages import routes as messages_api
from app.features.retrieval import routes as rag_api
from app.features.retrieval.providers.ai_search import AISearchProvider
from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.providers.memory import MemoryRetrievalProvider
from app.features.retrieval.providers.postgres import PostgresRetrievalProvider
from app.features.retrieval.service import RetrievalService
from app.features.run.service import RunService
from app.features.spa import routes as spa_api
from app.features.title.title_generator import TitleGenerator
from app.features.web_search.providers.base import WebSearchProvider
from app.features.web_search.providers.duckduckgo import DuckDuckGoSearchProvider
from app.features.web_search.providers.internal import InternalSearchProvider
from app.features.web_search.service import WebSearchService
from app.infra.cache.cached_authz_repository import CachedAuthzRepository
from app.infra.cache.cached_message_repository import CachedMessageRepository
from app.infra.client.cosmos_client import CosmosClientProvider, ensure_cosmos_resources
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
    LocalBlobStorage,
    MemoryBlobStorage,
)


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
        case "local":
            return LocalBlobStorage(app_config)
        case _:
            raise RuntimeError("unreachable")


def _build_run_service(
    app_config: AppConfig, chat_caps: ChatCapabilities, web_search: WebSearchService
) -> RunService:
    """Construct the run service for chat execution.

    Args:
        app_config: Application configuration.
        chat_caps: Chat capability configuration.
        web_search: Web search service instance.

    Returns:
        RunService: Run service instance.
    """
    provider_streamers: dict[str, ChatStreamer] = {}
    model_to_provider: dict[str, str] = {}
    for provider, models in chat_caps.providers.items():
        for model_id in models:
            if model_id in model_to_provider:
                raise RuntimeError(f"Model '{model_id}' is configured for multiple providers.")
            model_to_provider[model_id] = provider

    if chat_caps.has_provider("memory"):
        provider_streamers["memory"] = MemoryStreamer()
    if chat_caps.has_provider("azure"):
        provider_streamers["azure"] = AzureOpenAIStreamer(app_config)
    if chat_caps.has_provider("ollama"):
        provider_streamers["ollama"] = OllamaStreamer(app_config)

    if not provider_streamers:
        provider_streamers["memory"] = MemoryStreamer()
        model_to_provider["dummy"] = "memory"

    default_model_id = None
    if app_config.chat_default_model in model_to_provider:
        default_model_id = app_config.chat_default_model
    elif len(model_to_provider) == 1:
        default_model_id = next(iter(model_to_provider))

    streamer = MultiChatStreamer(
        provider_streamers,
        model_to_provider,
        default_model_id=default_model_id,
    )
    return RunService(
        streamer,
        TitleGenerator(app_config, streamer),
        web_search,
        fetch_web_search_content=app_config.web_search_fetch_content,
    )


def _build_web_search_service(settings: Settings) -> WebSearchService:
    """Construct the web search service based on settings.

    Args:
        settings: Application settings.

    Returns:
        WebSearchService: Configured web search service.
    """
    providers: dict[str, WebSearchProvider] = {}
    if settings.web_search_internal_url:
        providers["internal"] = InternalSearchProvider(
            settings.web_search_internal_url,
            api_key=settings.web_search_internal_api_key,
            auth_header=settings.web_search_internal_auth_header,
        )
    providers["duckduckgo"] = DuckDuckGoSearchProvider()

    if settings.web_search_engines_set:
        providers = {
            key: provider
            for key, provider in providers.items()
            if key in settings.web_search_engines_set
        }

    return WebSearchService(
        providers,
        default_engine=settings.web_search_default_engine or None,
    )


def _build_retrieval_service(settings: Settings) -> RetrievalService:
    """Construct the retrieval service based on settings.

    Args:
        settings: Application settings.

    Returns:
        RetrievalService: Configured retrieval service.
    """
    providers: dict[str, RetrievalProvider] = {
        "memory": MemoryRetrievalProvider(),
        "ai-search": AISearchProvider(
            settings.retrieval_ai_search_url,
            api_key=settings.retrieval_ai_search_api_key,
            auth_header=settings.retrieval_ai_search_auth_header,
        ),
        "postgres": PostgresRetrievalProvider(
            settings.retrieval_pg_dsn,
            settings.retrieval_pg_table,
            settings.retrieval_pg_text_column,
            settings.retrieval_pg_url_column,
            settings.retrieval_pg_embedding_column,
            settings.retrieval_pg_source_column,
        ),
    }
    return RetrievalService(
        providers,
        default_provider=settings.retrieval_default_provider or "memory",
    )


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

    app.state.cosmos_client_provider = None
    if app.state.storage_capabilities.db_backend == "azure":
        cosmos_client_provider = CosmosClientProvider(app.state.app_config)
        app.state.cosmos_client_provider = cosmos_client_provider

        await ensure_cosmos_resources(
            cosmos_client_provider,
            conversations_container=app.state.app_config.cosmos_conversations_container,
            messages_container=app.state.app_config.cosmos_messages_container,
            users_container=app.state.app_config.cosmos_users_container,
            tenants_container=app.state.app_config.cosmos_tenants_container,
            useridentities_container=app.state.app_config.cosmos_useridentities_container,
            provisioning_container=app.state.app_config.cosmos_provisioning_container,
        )

    repository = create_repository_factory(
        app.state.app_config,
        app.state.storage_capabilities,
        cosmos_provider=app.state.cosmos_client_provider,
        init_tenants=TENANTS,
        init_users=USERS,
        init_user_identities=USER_IDENTITIES,
        init_provisioning=PROVISIONING,
    )

    app.state.authz_repository = CachedAuthzRepository(
        repository.authz(),
        ttl_seconds=app.state.app_config.authz_cache_ttl_seconds,
        max_size=app.state.app_config.authz_cache_max_size,
    )
    app.state.authz_service = AuthzService(app.state.authz_repository)
    app.state.conversation_repository = repository.conversations()
    app.state.message_repository = CachedMessageRepository(
        repository.messages(),
        ttl_seconds=app.state.app_config.messages_cache_ttl_seconds,
        max_bytes=app.state.app_config.messages_cache_max_bytes,
    )
    app.state.usage_repository = repository.usage()

    app.state.blob_storage = _build_blob_storage(
        app.state.app_config, app.state.storage_capabilities
    )
    app.state.web_search_service = _build_web_search_service(settings)
    app.state.retrieval_service = _build_retrieval_service(settings)
    app.state.run_service = _build_run_service(
        app.state.app_config,
        app.state.chat_capabilities,
        app.state.web_search_service,
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

        logger.info("<*> Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = Settings()
    app_config = settings.to_app_config()
    log_level = app_config.log_level
    logging.config.dictConfig(build_logging_config(log_level=log_level.value))
    logger = logging.getLogger(__name__)

    configure_telemetry(app_config)

    frontend_dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"

    app = FastAPI(lifespan=lifespan)
    instrument_app(app, app_config)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions with a JSON error response.

        Args:
            request: Incoming request.
            exc: Raised exception instance.

        Returns:
            JSONResponse: Error response with HTTP 500.
        """
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"},
        )

    if frontend_dist_path.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=frontend_dist_path / "assets"),
            name="assets",
        )
        logger.info("Serving static files from %s", frontend_dist_path / "assets")
    else:
        logger.warning("Frontend dist directory not found at %s", frontend_dist_path)

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

    # ===== routers =====
    app.include_router(authz_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(capabilities_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(conversations_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(messages_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(chat_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(file_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(rag_api.router, prefix="/api", responses=common_error_responses)
    app.include_router(health_api.router, responses=common_error_responses)
    app.include_router(
        spa_api.create_spa_router(frontend_dist_path),
        responses=common_error_responses,
    )

    return app
