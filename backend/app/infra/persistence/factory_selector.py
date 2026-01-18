from logging import getLogger
from pathlib import Path

from app.core.config import AppConfig, StorageCapabilities
from app.features.authz.models import (
    ProvisioningRecord,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.infra.client.cosmos_client import CosmosClientProvider
from app.infra.client.firestore_client import FirestoreClientProvider
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
from app.infra.repository.cosmos.cosmos_jobs_repository import CosmosJobRepository
from app.infra.repository.local.local_authz_repository import LocalAuthzRepository
from app.infra.repository.local.local_conversations_repository import (
    LocalConversationRepository,
)
from app.infra.repository.local.local_messages_repository import LocalMessageRepository
from app.infra.repository.local.local_jobs_repository import LocalJobRepository
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)
from app.infra.repository.memory.memory_jobs_repository import MemoryJobRepository
from app.infra.storage.usage_buffer import create_usage_repository

logger = getLogger(__name__)


class _CosmosRepositoryFactory:
    """Cosmos DB backed repository factory."""

    def __init__(
        self,
        provider: CosmosClientProvider,
        config: AppConfig,
    ) -> None:
        self._provider = provider
        self._config = config

    async def authz(self):
        return CosmosAuthzRepository(
            users_container=self._provider.get_container(self._config.users_container),
            tenants_container=self._provider.get_container(self._config.tenants_container),
            identities_container=self._provider.get_container(
                self._config.useridentities_container
            ),
            provisioning_container=self._provider.get_container(
                self._config.provisioning_container
            ),
        )

    async def conversations(self):
        return CosmosConversationRepository(
            self._provider.get_container(self._config.conversations_container)
        )

    async def messages(self):
        return CosmosMessageRepository(
            self._provider.get_container(self._config.messages_container)
        )

    async def jobs(self):
        return CosmosJobRepository(self._provider.get_container(self._config.jobs_container))

    async def usage(self):
        return create_usage_repository(self._config)


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

    async def authz(self):
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

    async def conversations(self):
        return MemoryConversationRepository()

    async def messages(self):
        return MemoryMessageRepository()

    async def jobs(self):
        return MemoryJobRepository()

    async def usage(self):
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
        self._path.mkdir(parents=True, exist_ok=True)
        self._tenants = tenants
        self._users = users
        self._user_identities = user_identities
        self._provisioning = provisioning

    async def authz(self):
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

    async def conversations(self):
        return LocalConversationRepository(self._path)

    async def messages(self):
        return LocalMessageRepository(self._path)

    async def jobs(self):
        return LocalJobRepository(self._path)

    async def usage(self):
        return create_usage_repository(self._config)


class _FirestoreRepositoryFactory:
    """Firestore-backed repository factory."""

    def __init__(
        self,
        provider: FirestoreClientProvider,
        config: AppConfig,
    ) -> None:
        self._provider = provider
        self._config = config
        self._client = None
        try:
            from google.cloud import firestore as _firestore
        except ImportError as exc:
            raise RuntimeError("google-cloud-firestore is required for DB_BACKEND=gcp") from exc
        self._firestore = _firestore
        from app.infra.repository.firestore.firestore_authz_repository import (
            FirestoreAuthzRepository,
        )
        from app.infra.repository.firestore.firestore_conversations_repository import (
            FirestoreConversationRepository,
        )
        from app.infra.repository.firestore.firestore_messages_repository import (
            FirestoreMessageRepository,
        )
        from app.infra.repository.firestore.firestore_jobs_repository import (
            FirestoreJobRepository,
        )

        self._authz_repo = FirestoreAuthzRepository
        self._conversation_repo = FirestoreConversationRepository
        self._message_repo = FirestoreMessageRepository
        self._job_repo = FirestoreJobRepository

    async def _get_client(self):
        """Get Firestore client asynchronously."""
        if self._client is None:
            self._client = await self._provider.get_client()
        return self._client

    async def authz(self):
        client = await self._get_client()
        return self._authz_repo(
            tenants_collection=client.collection(self._config.tenants_container),
            users_collection=client.collection(self._config.users_container),
            identities_collection=client.collection(self._config.useridentities_container),
            provisioning_collection=client.collection(self._config.provisioning_container),
        )

    async def conversations(self):
        client = await self._get_client()
        return self._conversation_repo(client.collection(self._config.conversations_container))

    async def messages(self):
        client = await self._get_client()
        return self._message_repo(client.collection(self._config.messages_container))

    async def jobs(self):
        client = await self._get_client()
        return self._job_repo(client.collection(self._config.jobs_container))

    async def usage(self):
        return create_usage_repository(self._config)


def create_repository_factory(
    app_config: AppConfig,
    storage_caps: StorageCapabilities,
    *,
    cosmos_provider: CosmosClientProvider | None = None,
    firestore_provider: FirestoreClientProvider | None = None,
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
        firestore_provider: Firestore client provider (required for GCP backend).

    Returns:
        RepositoryFactory: Factory for creating repositories.

    Raises:
        RuntimeError: If the backend is unsupported or misconfigured.
    """
    logger.info("repository.factory.select db_backend=%s", storage_caps.db_backend)
    match storage_caps.db_backend:
        case "memory":
            logger.info("repository.factory.init backend=memory")
            return _MemoryRepositoryFactory(
                config=app_config,
                tenants=init_tenants or TENANTS,
                users=init_users or USERS,
                user_identities=init_user_identities or USER_IDENTITIES,
                provisioning=init_provisioning or PROVISIONING,
            )

        case "local":
            logger.info(
                "repository.factory.init backend=local path=%s", app_config.local_storage_path
            )
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

            logger.info("repository.factory.init backend=azure")
            return _CosmosRepositoryFactory(
                provider=cosmos_provider,
                config=app_config,
            )
        case "gcp":
            if firestore_provider is None:
                raise RuntimeError("FirestoreClientProvider is required for gcp backend")

            logger.info(
                "repository.factory.init backend=gcp project_id=%s", app_config.gcp_project_id
            )
            return _FirestoreRepositoryFactory(
                provider=firestore_provider,
                config=app_config,
            )

        case _:
            raise RuntimeError(f"Unsupported db backend: {storage_caps.db_backend}")
