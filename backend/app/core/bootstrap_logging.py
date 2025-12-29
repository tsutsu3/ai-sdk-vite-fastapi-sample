import json
import logging

from app.core.config import (
    AppConfig,
    ChatCapabilities,
    StorageCapabilities,
)

logger = logging.getLogger(__name__)


_MASK_KEYS = (
    "key",
    "token",
    "secret",
    "password",
    "connection_string",
)


def _should_mask(key: str) -> bool:
    return any(part in key.lower() for part in _MASK_KEYS)


def _mask_secrets(payload: dict[str, object]) -> dict[str, object]:
    masked: dict[str, object] = {}
    for key, value in payload.items():
        if _should_mask(key) and value:
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


def log_app_configuration(
    app_config: AppConfig,
    storage_caps: StorageCapabilities,
    chat_caps: ChatCapabilities,
) -> None:
    """Log effective application configuration at startup.

    Args:
        app_config: Resolved application configuration.
        storage_caps: Storage capability configuration.
        chat_caps: Chat capability configuration.
    """
    config_payload = {
        "app_config": _mask_secrets(app_config.model_dump(mode="json")),
        "storage_capabilities": storage_caps.model_dump(mode="json"),
        "chat_capabilities": chat_caps.model_dump(mode="json"),
    }
    logger.info("Application configuration: %s", json.dumps(config_payload, ensure_ascii=True))
