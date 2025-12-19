from contextlib import asynccontextmanager
import logging
import logging.config
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.logging_config import build_logging_config
from app.startup import load_repo_config, load_app_config
from app.features.authz import authz_api
from app.features.chat import chat_api
from app.features.conversations import conversations_api
from app.features.health import health_api
from app.features.spa import spa_api

from app.features.authz.repository.memory_authz_repository import MemoryAuthzRepository
from app.features.authz.repository.dummy_authz_repository import DummyAuthzRepository
from app.features.conversations.repository.memory_conversation_repository import (
    MemoryConversationRepository,
)
from app.features.chat.stream_service import ChatStreamService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger(__name__)

    logger.info("<*> Application startup begin")

    repo_config = load_repo_config()
    app.state.repo_config = repo_config

    app.state.app_config = load_app_config()

    # ===== authz repository =====
    match repo_config.authz_repository:
        case "memory":
            app.state.authz_repository = MemoryAuthzRepository()
        case "dummy":
            app.state.authz_repository = DummyAuthzRepository()
        case _:
            raise RuntimeError("unreachable")

    # ===== conversation repository =====
    match repo_config.conversation_repository:
        case "memory":
            app.state.conversation_repository = MemoryConversationRepository()
        case _:
            raise RuntimeError("unreachable")

    # ===== chat stream service =====
    match repo_config.chat_stream_service:
        case "memory":
            app.state.chat_stream_service = ChatStreamService()
        case _:
            raise RuntimeError("unreachable")

    logger.info("Log level set to %s", app.state.app_config.log_level.value)

    logger.info(
        "Repository config loaded: authz=%s conversation=%s chat=%s",
        app.state.repo_config.authz_repository,
        app.state.repo_config.conversation_repository,
        app.state.repo_config.chat_stream_service,
    )

    yield

    logger.info("<*> Application shutdown complete")


def create_app() -> FastAPI:
    log_level = load_app_config().log_level
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
    app.include_router(health_api.router)
    app.include_router(authz_api.router)
    app.include_router(conversations_api.router)
    app.include_router(chat_api.router)
    app.include_router(spa_api.create_spa_router(frontend_dist_path))

    return app


app = create_app()
