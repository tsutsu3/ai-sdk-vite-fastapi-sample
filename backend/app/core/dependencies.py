from typing import cast

from fastapi import Request

from app.core.config import AppConfig, ChatCapabilities, StorageCapabilities
from app.features.authz.ports import AuthzRepository
from app.features.authz.service import AuthzService
from app.features.chat.run.service import RunService
from app.features.conversations.ports import ConversationRepository
from app.features.jobs.ports import JobRepository
from app.features.messages.ports import MessageRepository
from app.features.usage.ports import UsageRepository
from app.infra.client.cosmos_client import CosmosClientProvider
from app.infra.client.firestore_client import FirestoreClientProvider
from app.shared.ports import BlobStorage


def get_authz_repository(request: Request) -> AuthzRepository:
    """Resolve the authz repository from app state.

    Args:
        request: Incoming request.

    Returns:
        AuthzRepository: Authorization repository.
    """
    return cast(AuthzRepository, request.app.state.authz_repository)


def get_authz_service(request: Request) -> AuthzService:
    """Resolve the authz service from app state."""
    return cast(AuthzService, request.app.state.authz_service)


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


def get_job_repository(request: Request) -> JobRepository:
    """Resolve the job repository from app state."""
    return cast(JobRepository, request.app.state.job_repository)


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


def get_app_config(request: Request) -> AppConfig:
    return cast(AppConfig, request.app.state.app_config)


def get_storage_capabilities(request: Request) -> StorageCapabilities:
    return cast(StorageCapabilities, request.app.state.storage_capabilities)


def get_chat_capabilities(request: Request) -> ChatCapabilities:
    return cast(ChatCapabilities, request.app.state.chat_capabilities)


def get_cosmos_client_provider(request: Request) -> CosmosClientProvider | None:
    return cast(CosmosClientProvider | None, request.app.state.cosmos_client_provider)


def get_firestore_client_provider(request: Request) -> FirestoreClientProvider | None:
    return cast(FirestoreClientProvider | None, request.app.state.firestore_client_provider)
