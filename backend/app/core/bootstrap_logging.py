import logging
from typing import Iterable

from app.core.config import (
    AppConfig,
    ChatCapabilities,
    StorageCapabilities,
)

logger = logging.getLogger(__name__)


def _join(items: Iterable[str]) -> str:
    return ", ".join(items) if items else "-"


def log_app_configuration(
    app_config: AppConfig,
    storage_caps: StorageCapabilities,
    chat_caps: ChatCapabilities,
) -> None:
    """
    Log effective application configuration at startup.
    This logs capabilities and enabled features, not implementation classes.
    """

    logger.info("====== Application Configuration ======")

    # --- Logging / Common ---
    logger.info("Log level            : %s", app_config.log_level.value)

    # --- Storage ---
    logger.info(
        "Storage backends     : db=%s, blob=%s",
        storage_caps.db_backend.value,
        storage_caps.blob_backend.value,
    )

    # --- Chat providers & models ---
    if not chat_caps.providers:
        logger.info("Chat providers       : -")
    else:
        parts: list[str] = []
        for provider, models in sorted(chat_caps.providers.items()):
            if models:
                parts.append(f"{provider}[{_join(sorted(models))}]")
            else:
                parts.append(provider)
        logger.info("Chat providers       : %s", _join(parts))

        parts = []
        for provider, models in sorted(chat_caps.providers.items()):
            names: list[str] = []
            for model in sorted(models):
                name = chat_caps.model_names.get(model, model)
                names.append(name)

            if names:
                parts.append(f"{provider}[{_join(sorted(names))}]")

        logger.info("Chat capabilities    : %s", _join(parts))

    if app_config.chat_title_model:
        logger.info("Chat title model     : %s", app_config.chat_title_model)

    # --- Azure specific (only if enabled) ---
    if "azure" in chat_caps.providers:
        logger.info(
            "Azure OpenAI version : %s",
            app_config.azure_openai_api_version,
        )

    logger.info("=======================================")
