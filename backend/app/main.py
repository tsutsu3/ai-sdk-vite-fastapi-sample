import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import authz as authz_api
from app.api import capabilities as capabilities_api
from app.api import chat as chat_api
from app.api import conversations as conversations_api
from app.api import file as file_api
from app.api import health as health_api
from app.api import messages as messages_api
from app.api import spa as spa_api
from app.core.bootstrap_logging import log_app_configuration
from app.core.config import Settings
from app.features.authz.repository.cached_authz_repository import CachedAuthzRepository
from app.features.authz.repository.cosmos_authz_repository import (
    CosmosAuthzRepository,
)
from app.features.authz.repository.memory_authz_repository import MemoryAuthzRepository
from app.features.authz.repository.authz_repository import AuthzRepository
from app.features.chat.streamers import (
    AzureOpenAIStreamer,
    MemoryStreamer,
    MultiChatStreamer,
    OllamaStreamer,
    ChatStreamer,
)
from app.features.conversations.repository.cosmos_conversation_repository import (
    CosmosConversationRepository,
)
from app.features.conversations.repository.local_conversation_repository import (
    LocalConversationRepository,
)
from app.features.conversations.repository.memory_conversation_repository import (
    MemoryConversationRepository,
)
from app.features.messages.repository.cosmos_message_repository import (
    CosmosMessageRepository,
)
from app.features.messages.repository.local_message_repository import (
    LocalMessageRepository,
)
from app.features.messages.repository.memory_message_repository import (
    MemoryMessageRepository,
)
from app.features.run.service import RunService
from app.features.title.title_generator import TitleGenerator
from app.features.usage.repository.cosmos_usage_repository import (
    CosmosUsageRepository,
)
from app.features.usage.repository.local_usage_repository import (
    LocalUsageRepository,
)
from app.features.usage.repository.memory_usage_repository import (
    MemoryUsageRepository,
)
from app.features.web_search.providers.duckduckgo import DuckDuckGoSearchProvider
from app.features.web_search.providers.internal import InternalSearchProvider
from app.features.web_search.providers.base import WebSearchProvider
from app.features.web_search.service import WebSearchService
from app.logging_config import build_logging_config
from app.shared.infra.blob_storage import (
    AzureBlobStorage,
    LocalBlobStorage,
    MemoryBlobStorage,
)
from app.shared.infra.cosmos_client import ensure_cosmos_resources


def _local_storage_path(app_config) -> Path:
    return Path(app_config.local_storage_path).resolve()


async def _ensure_cosmos(app_config, storage_caps) -> None:
    if (
        app_config.cosmos_database
        and app_config.cosmos_endpoint
        and app_config.cosmos_key
        and storage_caps.db_backend == "azure"
    ):
        await ensure_cosmos_resources(app_config)


def _build_authz_repository(app_config, storage_caps) -> AuthzRepository:
    match storage_caps.db_backend:
        case "memory":
            base_repo: AuthzRepository = MemoryAuthzRepository()
        case "azure":
            base_repo = CosmosAuthzRepository(app_config)
        case "local":
            base_repo = MemoryAuthzRepository()
        case _:
            raise RuntimeError("unreachable")
    return CachedAuthzRepository(
        base_repo,
        ttl_seconds=app_config.authz_cache_ttl_seconds,
        max_size=app_config.authz_cache_max_size,
    )


def _build_conversation_repository(app_config, storage_caps):
    match storage_caps.db_backend:
        case "memory":
            return MemoryConversationRepository()
        case "azure":
            return CosmosConversationRepository(app_config)
        case "local":
            return LocalConversationRepository(_local_storage_path(app_config))
        case _:
            raise RuntimeError("unreachable")


def _build_message_repository(app_config, storage_caps):
    match storage_caps.db_backend:
        case "memory":
            return MemoryMessageRepository()
        case "azure":
            return CosmosMessageRepository(app_config)
        case "local":
            return LocalMessageRepository(_local_storage_path(app_config))
        case _:
            raise RuntimeError("unreachable")


def _build_usage_repository(app_config, storage_caps):
    match storage_caps.db_backend:
        case "memory":
            return MemoryUsageRepository()
        case "azure":
            return CosmosUsageRepository(app_config)
        case "local":
            return LocalUsageRepository(_local_storage_path(app_config))
        case _:
            raise RuntimeError("unreachable")


def _build_blob_storage(app_config, storage_caps):
    match storage_caps.blob_backend:
        case "memory":
            return MemoryBlobStorage()
        case "azure":
            return AzureBlobStorage(app_config)
        case "local":
            return LocalBlobStorage(app_config)
        case _:
            raise RuntimeError("unreachable")


def _build_run_service(app_config, chat_caps, web_search: WebSearchService) -> RunService:
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
    if len(model_to_provider) == 1:
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger(__name__)

    logger.info("<*> Application startup begin")

    settings = Settings()

    app.state.app_config = settings.to_app_config()
    app.state.storage_capabilities = settings.to_storage_capabilities()
    app.state.chat_capabilities = settings.to_chat_capabilities()

    await _ensure_cosmos(app.state.app_config, app.state.storage_capabilities)

    app.state.authz_repository = _build_authz_repository(
        app.state.app_config, app.state.storage_capabilities
    )
    app.state.conversation_repository = _build_conversation_repository(
        app.state.app_config, app.state.storage_capabilities
    )
    app.state.message_repository = _build_message_repository(
        app.state.app_config, app.state.storage_capabilities
    )
    app.state.usage_repository = _build_usage_repository(
        app.state.app_config, app.state.storage_capabilities
    )
    app.state.blob_storage = _build_blob_storage(
        app.state.app_config, app.state.storage_capabilities
    )
    app.state.web_search_service = _build_web_search_service(settings)
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

    yield

    logger.info("<*> Application shutdown complete")


def create_app() -> FastAPI:
    settings = Settings()
    app_config = settings.to_app_config()
    log_level = app_config.log_level
    logging.config.dictConfig(build_logging_config(log_level=log_level.value))
    logger = logging.getLogger(__name__)

    frontend_dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"

    app = FastAPI(lifespan=lifespan)

    if frontend_dist_path.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=frontend_dist_path / "assets"),
            name="assets",
        )
        logger.info("Serving static files from %s", frontend_dist_path / "assets")
    else:
        logger.warning("Frontend dist directory not found at %s", frontend_dist_path)

    # ===== routers =====
    app.include_router(authz_api.router, prefix="/api")
    app.include_router(capabilities_api.router, prefix="/api")
    app.include_router(conversations_api.router, prefix="/api")
    app.include_router(messages_api.router, prefix="/api")
    app.include_router(chat_api.router, prefix="/api")
    app.include_router(file_api.router, prefix="/api")
    app.include_router(health_api.router)
    app.include_router(spa_api.create_spa_router(frontend_dist_path))

    return app


app = create_app()
