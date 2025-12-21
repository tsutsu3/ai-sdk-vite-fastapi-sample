from typing import cast

from fastapi import Request

from app.features.authz.repository.authz_repository import AuthzRepository
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.run.service import RunService
from app.features.usage.ports import UsageRepository
from app.shared.infra.blob_storage import BlobStorage


def get_authz_repository(request: Request) -> AuthzRepository:
    return cast(AuthzRepository, request.app.state.authz_repository)


def get_conversation_repository(request: Request) -> ConversationRepository:
    return cast(
        ConversationRepository,
        request.app.state.conversation_repository,
    )


def get_message_repository(request: Request) -> MessageRepository:
    return cast(MessageRepository, request.app.state.message_repository)


def get_usage_repository(request: Request) -> UsageRepository:
    return cast(UsageRepository, request.app.state.usage_repository)


def get_blob_storage(request: Request) -> BlobStorage:
    return cast(BlobStorage, request.app.state.blob_storage)


def get_run_service(request: Request) -> RunService:
    return cast(RunService, request.app.state.run_service)
