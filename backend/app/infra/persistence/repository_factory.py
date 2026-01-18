from typing import Protocol

from app.features.authz.ports import AuthzRepository
from app.features.conversations.ports import ConversationRepository
from app.features.jobs.ports import JobRepository
from app.features.messages.ports import MessageRepository
from app.features.usage.ports import UsageRepository


class RepositoryFactory(Protocol):
    """Factory interface for creating repositories.

    This abstraction hides the concrete storage backend
    (Cosmos, Firestore, Local, etc.) from application code.
    """

    async def authz(self) -> AuthzRepository:
        """Return an authorization repository."""
        raise NotImplementedError

    async def conversations(self) -> ConversationRepository:
        """Return a conversation repository."""
        raise NotImplementedError

    async def messages(self) -> MessageRepository:
        """Return a message repository."""
        raise NotImplementedError

    async def jobs(self) -> JobRepository:
        """Return a job repository."""
        raise NotImplementedError

    async def usage(self) -> UsageRepository:
        """Return a usage repository."""
        raise NotImplementedError
