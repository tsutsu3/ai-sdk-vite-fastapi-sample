from pydantic import BaseModel


class RepoConfig(BaseModel, frozen=True):
    authz_repository: str
    conversation_repository: str
    chat_stream_service: str
