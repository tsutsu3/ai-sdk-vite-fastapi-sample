import os

from app.core.config import RepoConfig, AppConfig, LogLevelEnum

SUPPORTED = {
    "authz_repository": {"memory", "dummy"},
    "conversation_repository": {"memory"},
    "chat_stream_service": {"memory"},
}


def getenv_with_default(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None:
        return default
    value = value.strip()
    return value or default


def load_app_config() -> AppConfig:
    log_level = getenv_with_default("LOG_LEVEL", "INFO").upper()
    return AppConfig(log_level=LogLevelEnum(log_level))


def load_repo_config() -> RepoConfig:
    authz = getenv_with_default("AUTHZ_REPOSITORY", "memory").lower()
    conv = getenv_with_default("CONVERSATION_REPOSITORY", "memory").lower()
    chat = getenv_with_default("CHAT_STREAM_SERVICE", "memory").lower()

    if authz not in SUPPORTED["authz_repository"]:
        raise RuntimeError(f"Unsupported AUTHZ_REPOSITORY={authz}")

    if conv not in SUPPORTED["conversation_repository"]:
        raise RuntimeError(f"Unsupported CONVERSATION_REPOSITORY={conv}")

    if chat not in SUPPORTED["chat_stream_service"]:
        raise RuntimeError(f"Unsupported CHAT_STREAM_SERVICE={chat}")

    return RepoConfig(
        authz_repository=authz,
        conversation_repository=conv,
        chat_stream_service=chat,
    )
