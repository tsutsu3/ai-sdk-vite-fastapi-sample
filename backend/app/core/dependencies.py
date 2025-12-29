from typing import cast

from fastapi import Request

from app.features.authz.ports import AuthzRepository
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.retrieval.service import RetrievalService
from app.features.run.service import RunService
from app.features.usage.ports import UsageRepository
from app.features.web_search.service import WebSearchService
from app.shared.ports import BlobStorage


def get_authz_repository(request: Request) -> AuthzRepository:
    """Resolve the authz repository from app state.

    Args:
        request: Incoming request.

    Returns:
        AuthzRepository: Authorization repository.
    """
    return cast(AuthzRepository, request.app.state.authz_repository)


def get_conversation_repository(request: Request) -> ConversationRepository:
    """Resolve the conversation repository from app state.

    Args:
        request: Incoming request.

    Returns:
        ConversationRepository: Conversation repository.
    """
    return cast(
        ConversationRepository,
        request.app.state.conversation_repository,
    )


def get_message_repository(request: Request) -> MessageRepository:
    """Resolve the message repository from app state.

    Args:
        request: Incoming request.

    Returns:
        MessageRepository: Message repository.
    """
    return cast(MessageRepository, request.app.state.message_repository)


def get_usage_repository(request: Request) -> UsageRepository:
    """Resolve the usage repository from app state.

    Args:
        request: Incoming request.

    Returns:
        UsageRepository: Usage repository.
    """
    return cast(UsageRepository, request.app.state.usage_repository)


def get_blob_storage(request: Request) -> BlobStorage:
    """Resolve the blob storage backend from app state.

    Args:
        request: Incoming request.

    Returns:
        BlobStorage: Blob storage backend.
    """
    return cast(BlobStorage, request.app.state.blob_storage)


def get_run_service(request: Request) -> RunService:
    """Resolve the run service from app state.

    Args:
        request: Incoming request.

    Returns:
        RunService: Run service instance.
    """
    return cast(RunService, request.app.state.run_service)


def get_web_search_service(request: Request) -> WebSearchService:
    """Resolve the web search service from app state.

    Args:
        request: Incoming request.

    Returns:
        WebSearchService: Web search service.
    """
    return cast(WebSearchService, request.app.state.web_search_service)


def get_retrieval_service(request: Request) -> RetrievalService:
    """Resolve the retrieval service from app state.

    Args:
        request: Incoming request.

    Returns:
        RetrievalService: Retrieval service.
    """
    return cast(RetrievalService, request.app.state.retrieval_service)
