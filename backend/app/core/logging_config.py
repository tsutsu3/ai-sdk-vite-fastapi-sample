import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Format logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "tenant_id": getattr(record, "tenant_id", None),
            "user_id": getattr(record, "user_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


class AccessJsonFormatter(logging.Formatter):
    """Format access logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "tenant_id": getattr(record, "tenant_id", None),
            "user_id": getattr(record, "user_id", None),
            "client_addr": getattr(record, "client_addr", None),
            "request_line": getattr(record, "request_line", None),
            "status_code": getattr(record, "status_code", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def build_logging_config(log_level: str) -> dict[str, object]:
    """Build the logging configuration dictionary.

    Args:
        log_level: Log level name.

    Returns:
        dict[str, object]: Logging configuration for dictConfig.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "app.core.logging_config.JsonFormatter",
            },
            "access": {
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
                "formatter": "default",
                "filters": ["request_context"],
                "stream": "ext://sys.stdout",
            },
            "access_console": {
                "class": "logging.StreamHandler",
                "formatter": "access",
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
        try:
            from app.features.authz.request_context import (
                get_current_tenant_id,
                get_current_user_id,
            )

            tenant_id = get_current_tenant_id()
            user_id = get_current_user_id()
        except Exception:
            tenant_id = None
            user_id = None
        record.tenant_id = tenant_id
        record.user_id = user_id
        return True
