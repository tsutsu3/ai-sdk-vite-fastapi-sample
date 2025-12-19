from contextlib import asynccontextmanager
import logging
import logging.config
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.logging_config import LOGGING_CONFIG
from app.startup import load_repo_config
from app.features.authz import authz_api
from app.features.chat import chat_api
from app.features.conversations import conversations_api
from app.features.health import health_api
from app.features.spa import spa_api


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger(__name__)

    logger.info("<*> Application startup begin")

    app.state.repo_config = load_repo_config()

    logger.info(
        "Repository config loaded: authz=%s conversation=%s chat=%s",
        app.state.repo_config.authz_repository,
        app.state.repo_config.conversation_repository,
        app.state.repo_config.chat_stream_service,
    )

    yield

    logger.info("<*> Application shutdown complete")


def create_app() -> FastAPI:
    logging.config.dictConfig(LOGGING_CONFIG)
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
