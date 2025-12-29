from logging import getLogger
from pathlib import Path

from azure.eventhub.aio import EventHubProducerClient

from app.core.config import AppConfig, StorageCapabilities
from app.features.authz.models import (
    ProvisioningRecord,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.infra.client.cosmos_client import CosmosClientProvider
from app.infra.fixtures.authz.local_data import (
    PROVISIONING,
    TENANTS,
    USER_IDENTITIES,
    USERS,
)
from app.infra.persistence.repository_factory import RepositoryFactory
from app.infra.repository.cosmos.cosmos_authz_repository import CosmosAuthzRepository
from app.infra.repository.cosmos.cosmos_conversations_repository import (
    CosmosConversationRepository,
)
from app.infra.repository.cosmos.cosmos_messages_repository import (
    CosmosMessageRepository,
)
from app.infra.repository.local.local_authz_repository import LocalAuthzRepository
from app.infra.repository.local.local_conversations_repository import (
    LocalConversationRepository,
)
from app.infra.repository.local.local_messages_repository import LocalMessageRepository
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)
from app.infra.storage.usage_buffer import create_usage_repository

logger = getLogger(__name__)


class _AzureRepositoryFactory:
    """Azure backed repository factory."""

    def __init__(
        self,
        provider: CosmosClientProvider,
        config: AppConfig,
        azure_eventhub_producer: EventHubProducerClient | None = None,
    ) -> None:
        self._provider = provider
        self._config = config
        self._azure_eventhub_producer = azure_eventhub_producer

    def authz(self):
        return CosmosAuthzRepository(
            users_container=self._provider.get_container(self._config.cosmos_users_container),
            tenants_container=self._provider.get_container(self._config.cosmos_tenants_container),
            identities_container=self._provider.get_container(
                self._config.cosmos_useridentities_container
            ),
            provisioning_container=self._provider.get_container(
                self._config.cosmos_provisioning_container
            ),
        )

    def conversations(self):
        return CosmosConversationRepository(
            self._provider.get_container(self._config.cosmos_conversations_container)
        )

    def messages(self):
        return CosmosMessageRepository(
            self._provider.get_container(self._config.cosmos_messages_container)
        )

    def usage(self):
        return create_usage_repository(
            self._config,
            azure_eventhub_producer=self._azure_eventhub_producer,
        )


class _MemoryRepositoryFactory:
    """In-memory repository factory (dummy / test)."""

    def __init__(
        self,
        config: AppConfig,
        tenants: dict[str, TenantRecord] | None = None,
        users: dict[str, UserRecord] | None = None,
        user_identities: dict[str, UserIdentityRecord] | None = None,
        provisioning: dict[str, ProvisioningRecord] | None = None,
    ) -> None:
        self._config = config
        self._tenants = tenants
        self._users = users
        self._user_identities = user_identities
        self._provisioning = provisioning

    def authz(self):
        logger.debug("Using memory authz repository")
        logger.debug("Initial tenants: %s", list(self._tenants.keys()) if self._tenants else [])
        logger.debug(
            "Initial provisioning records: %s",
            list(self._provisioning.keys()) if self._provisioning else [],
        )
        logger.debug(
            "Initial user identities: %s",
            list(self._user_identities.keys()) if self._user_identities else [],
        )
        logger.debug("Initial users: %s", list(self._users.keys()) if self._users else [])
        return MemoryAuthzRepository(
            tenants=self._tenants,
            users=self._users,
            user_identities=self._user_identities,
            provisioning=self._provisioning,
        )

    def conversations(self):
        return MemoryConversationRepository()

    def messages(self):
        return MemoryMessageRepository()

    def usage(self):
        return create_usage_repository(self._config)


class _LocalRepositoryFactory:
    """Local repository factory."""

    def __init__(
        self,
        config: AppConfig,
        tenants: dict[str, TenantRecord] | None = None,
        users: dict[str, UserRecord] | None = None,
        user_identities: dict[str, UserIdentityRecord] | None = None,
        provisioning: dict[str, ProvisioningRecord] | None = None,
    ) -> None:
        self._config = config
        self._path = Path(config.local_storage_path)
        self._tenants = tenants
        self._users = users
        self._user_identities = user_identities
        self._provisioning = provisioning

    def authz(self):
        logger.debug("Using local authz repository at %s", self._path)
        logger.debug("Initial tenants: %s", list(self._tenants.keys()) if self._tenants else [])
        logger.debug(
            "Initial provisioning records: %s",
            list(self._provisioning.keys()) if self._provisioning else [],
        )
        logger.debug(
            "Initial user identities: %s",
            list(self._user_identities.keys()) if self._user_identities else [],
        )
        logger.debug("Initial users: %s", list(self._users.keys()) if self._users else [])
        return LocalAuthzRepository(
            self._path,
            tenants=self._tenants,
            users=self._users,
            user_identities=self._user_identities,
            provisioning=self._provisioning,
        )

    def conversations(self):
        return LocalConversationRepository(self._path)

    def messages(self):
        return LocalMessageRepository(self._path)

    def usage(self):
        return create_usage_repository(self._config)


def create_repository_factory(
    app_config: AppConfig,
    storage_caps: StorageCapabilities,
    *,
    cosmos_provider: CosmosClientProvider | None = None,
    azure_eventhub_producer: EventHubProducerClient | None = None,
    init_tenants: dict[str, TenantRecord] | None = None,
    init_users: dict[str, UserRecord] | None = None,
    init_user_identities: dict[str, UserIdentityRecord] | None = None,
    init_provisioning: dict[str, ProvisioningRecord] | None = None,
) -> RepositoryFactory:
    """Create a repository factory for the configured storage backend.

    Args:
        app_config: Application configuration.
        storage_caps: Storage capability configuration.
        cosmos_provider: Cosmos client provider (required for Azure backend).

    Returns:
        RepositoryFactory: Factory for creating repositories.

    Raises:
        RuntimeError: If the backend is unsupported or misconfigured.
    """
    match storage_caps.db_backend:
        case "memory":
            return _MemoryRepositoryFactory(
                config=app_config,
                tenants=init_tenants or TENANTS,
                users=init_users or USERS,
                user_identities=init_user_identities or USER_IDENTITIES,
                provisioning=init_provisioning or PROVISIONING,
            )

        case "local":
            return _LocalRepositoryFactory(
                config=app_config,
                tenants=init_tenants or TENANTS,
                users=init_users or USERS,
                user_identities=init_user_identities or USER_IDENTITIES,
                provisioning=init_provisioning or PROVISIONING,
            )

        case "azure":
            if cosmos_provider is None:
                raise RuntimeError("CosmosClientProvider is required for azure backend")

            return _AzureRepositoryFactory(
                provider=cosmos_provider,
                config=app_config,
                azure_eventhub_producer=azure_eventhub_producer,
            )

        case _:
            raise RuntimeError(f"Unsupported db backend: {storage_caps.db_backend}")
