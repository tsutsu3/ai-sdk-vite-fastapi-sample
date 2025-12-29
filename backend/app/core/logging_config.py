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
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "access_console": {
                "class": "logging.StreamHandler",
                "formatter": "access",
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
