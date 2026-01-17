import json
import logging
from datetime import datetime, timezone


class TextFormatter(logging.Formatter):
    """Format logs as human-readable text."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class JsonFormatter(logging.Formatter):
    """Format logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "user_id": getattr(record, "user_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


class AccessTextFormatter(logging.Formatter):
    """Format access logs as human-readable text."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s - client=%(client_addr)s status=%(status_code)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        record.client_addr = getattr(record, "client_addr", "-")
        record.status_code = getattr(record, "status_code", "-")
        return super().format(record)


class AccessJsonFormatter(logging.Formatter):
    """Format access logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "user_id": getattr(record, "user_id", None),
            "client_addr": getattr(record, "client_addr", None),
            "request_line": getattr(record, "request_line", None),
            "status_code": getattr(record, "status_code", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def build_logging_config(log_level: str, log_format: str = "json") -> dict[str, object]:
    """Build the logging configuration dictionary.

    Args:
        log_level: Log level name.
        log_format: Log format ("json" or "text").

    Returns:
        dict[str, object]: Logging configuration for dictConfig.
    """
    default_formatter = "default_json" if log_format == "json" else "default_text"
    access_formatter = "access_json" if log_format == "json" else "access_text"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default_text": {
                "()": "app.core.logging_config.TextFormatter",
            },
            "default_json": {
                "()": "app.core.logging_config.JsonFormatter",
            },
            "access_text": {
                "()": "app.core.logging_config.AccessTextFormatter",
            },
            "access_json": {
                "()": "app.core.logging_config.AccessJsonFormatter",
            },
        },
        "filters": {
            "request_context": {
                "()": "app.core.logging_config.RequestContextFilter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": default_formatter,
                "filters": ["request_context"],
                "stream": "ext://sys.stdout",
            },
            "access_console": {
                "class": "logging.StreamHandler",
                "formatter": access_formatter,
                "filters": ["request_context"],
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access_console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }


class RequestContextFilter(logging.Filter):
    """Attach tenant/user ids from request context when available."""

    def filter(self, record: logging.LogRecord) -> bool:
        tenant_id = None
        user_id = None
        request_id = None
        try:
            from app.core.request_id import get_current_request_id
            from app.features.authz.request_context import (
                get_current_tenant_id,
                get_current_user_id,
            )

            tenant_id = get_current_tenant_id()
            user_id = get_current_user_id()
            request_id = get_current_request_id()
        except Exception:
            tenant_id = None
            user_id = None
            request_id = None
        record.tenant_id = tenant_id
        record.user_id = user_id
        record.request_id = request_id
        return True
