from pydantic import BaseModel, Field
from enum import Enum


class LogLevelEnum(str, Enum):
    critical = "CRITICAL"
    error = "ERROR"
    warning = "WARNING"
    info = "INFO"
    debug = "DEBUG"


class AppConfig(BaseModel, frozen=True):
    log_level: LogLevelEnum = Field(default=LogLevelEnum.info)


class RepoConfig(BaseModel, frozen=True):
    authz_repository: str
    conversation_repository: str
    chat_stream_service: str
