from app.features.authz.repository.authz_repository import AuthzRepository
from app.features.authz.repository.memory_authz_repository import MemoryAuthzRepository
from app.features.conversations.repository.conversation_repository import (
    ConversationRepository,
)
from app.features.conversations.repository.memory_conversation_repository import (
    MemoryConversationRepository,
)
from app.features.chat.stream_service import ChatStreamService


_authz_repo = MemoryAuthzRepository()
_conversation_repo = MemoryConversationRepository()
_chat_stream_service = ChatStreamService()


def get_authz_repository() -> AuthzRepository:
    return _authz_repo


def get_conversation_repository() -> ConversationRepository:
    return _conversation_repo


def get_chat_stream_service() -> ChatStreamService:
    return _chat_stream_service
