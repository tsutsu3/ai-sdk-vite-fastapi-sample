from typing import cast
from fastapi import Request

from app.features.authz.repository.authz_repository import AuthzRepository
from app.features.chat.stream_service import ChatStreamService
from app.features.conversations.repository.conversation_repository import (
    ConversationRepository,
)


def get_authz_repository(request: Request) -> AuthzRepository:
    return cast(AuthzRepository, request.app.state.authz_repository)


def get_conversation_repository(request: Request) -> ConversationRepository:
    return cast(
        ConversationRepository,
        request.app.state.conversation_repository,
    )


def get_chat_stream_service(request: Request) -> ChatStreamService:
    return cast(ChatStreamService, request.app.state.chat_stream_service)
