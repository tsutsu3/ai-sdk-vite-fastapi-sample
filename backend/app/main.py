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
from app.features.chat.streamers import (
    AzureOpenAIStreamer,
    MemoryStreamer,
    MultiChatStreamer,
    OllamaStreamer,
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
from app.logging_config import build_logging_config
from app.shared.infra.blob_storage import (
    AzureBlobStorage,
    LocalBlobStorage,
    MemoryBlobStorage,
)
from app.shared.infra.cosmos_client import ensure_cosmos_resources


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger(__name__)

    logger.info("<*> Application startup begin")

    settings = Settings()

    app.state.app_config = settings.to_app_config()
    app.state.storage_capabilities = settings.to_storage_capabilities()
    app.state.chat_capabilities = settings.to_chat_capabilities()

    if (
        app.state.app_config.cosmos_database
        and app.state.app_config.cosmos_endpoint
        and app.state.app_config.cosmos_key
        and app.state.storage_capabilities.db_backend == "azure"
    ):
        await ensure_cosmos_resources(app.state.app_config)

    # ===== authz repository =====
    match app.state.storage_capabilities.db_backend:
        case "memory":
            authz_repository = MemoryAuthzRepository()
        case "azure":
            authz_repository = CosmosAuthzRepository(app.state.app_config)
        case "local":
            authz_repository = MemoryAuthzRepository()
        case _:
            raise RuntimeError("unreachable")

    app.state.authz_repository = CachedAuthzRepository(
        authz_repository,
        ttl_seconds=app.state.app_config.authz_cache_ttl_seconds,
        max_size=app.state.app_config.authz_cache_max_size,
    )

    # ===== conversation repository =====
    match app.state.storage_capabilities.db_backend:
        case "memory":
            app.state.conversation_repository = MemoryConversationRepository()
        case "azure":
            app.state.conversation_repository = CosmosConversationRepository(app.state.app_config)
        case "local":
            app.state.conversation_repository = LocalConversationRepository(
                Path(app.state.app_config.local_storage_path).resolve()
            )
        case _:
            raise RuntimeError("unreachable")

    # ===== message repository =====
    match app.state.storage_capabilities.db_backend:
        case "memory":
            app.state.message_repository = MemoryMessageRepository()
        case "azure":
            app.state.message_repository = CosmosMessageRepository(app.state.app_config)
        case "local":
            app.state.message_repository = LocalMessageRepository(
                Path(app.state.app_config.local_storage_path).resolve()
            )
        case _:
            raise RuntimeError("unreachable")

    # ===== usage repository =====
    match app.state.storage_capabilities.db_backend:
        case "memory":
            app.state.usage_repository = MemoryUsageRepository()
        case "azure":
            app.state.usage_repository = CosmosUsageRepository(app.state.app_config)
        case "local":
            app.state.usage_repository = LocalUsageRepository(
                Path(app.state.app_config.local_storage_path).resolve()
            )
        case _:
            raise RuntimeError("unreachable")

    # ===== blob storage =====
    match app.state.storage_capabilities.blob_backend:
        case "memory":
            app.state.blob_storage = MemoryBlobStorage()
        case "azure":
            app.state.blob_storage = AzureBlobStorage(app.state.app_config)
        case "local":
            app.state.blob_storage = LocalBlobStorage(app.state.app_config)
        case _:
            raise RuntimeError("unreachable")

    # ===== run service =====
    provider_streamers = {}
    model_to_provider: dict[str, str] = {}
    for provider, models in app.state.chat_capabilities.providers.items():
        for model_id in models:
            if model_id in model_to_provider:
                raise RuntimeError(f"Model '{model_id}' is configured for multiple providers.")
            model_to_provider[model_id] = provider

    if app.state.chat_capabilities.has_provider("memory"):
        provider_streamers["memory"] = MemoryStreamer()
    if app.state.chat_capabilities.has_provider("azure"):
        provider_streamers["azure"] = AzureOpenAIStreamer(app.state.app_config)
    if app.state.chat_capabilities.has_provider("ollama"):
        provider_streamers["ollama"] = OllamaStreamer(app.state.app_config)

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
    app.state.run_service = RunService(
        streamer,
        TitleGenerator(app.state.app_config, streamer),
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
