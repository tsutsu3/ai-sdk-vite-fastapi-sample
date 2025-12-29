from azure.cosmos import PartitionKey
from azure.cosmos.aio import ContainerProxy, CosmosClient

from app.core.config import AppConfig

CONVERSATIONS_PARTITION_KEY = "/tenantId"
MESSAGES_PARTITION_KEY = "/tenantId/convId"
USERS_PARTITION_KEY = "/id"
TENANTS_PARTITION_KEY = "/id"
USERIDENTITIES_PARTITION_KEY = "/id"
PROVISIONING_PARTITION_KEY = "/email"


class CosmosClientProvider:
    """Provides access to a Cosmos DB client, database, and containers.

    This class is responsible for:
    - Creating and holding a CosmosClient instance
    - Resolving a database client
    - Resolving container clients

    It does NOT create databases or containers.
    Resource provisioning should be handled separately.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize the Cosmos client provider.

        Args:
            config: Application configuration containing Cosmos DB settings.

        Raises:
            RuntimeError: If required Cosmos configuration is missing.
        """
        if not config.cosmos_endpoint or not config.cosmos_key:
            raise RuntimeError("COSMOS_ENDPOINT or COSMOS_KEY is not configured.")

        self._client = CosmosClient(
            config.cosmos_endpoint,
            credential=config.cosmos_key,
        )
        self._database_name = config.cosmos_database
        self._database = self._client.get_database_client(self._database_name)

    @property
    def client(self) -> CosmosClient:
        """Return the underlying CosmosClient instance."""
        return self._client

    async def close(self) -> None:
        """Close the underlying Cosmos client."""
        await self._client.close()

    def get_container(self, container_name: str) -> ContainerProxy:
        """Resolve a Cosmos DB container client.

        Args:
            container_name: Name of the Cosmos DB container.

        Returns:
            ContainerProxy: Container client for the given name.
        """
        return self._database.get_container_client(container_name)


async def ensure_cosmos_resources(
    provider: CosmosClientProvider,
    *,
    conversations_container: str,
    messages_container: str,
    users_container: str,
    tenants_container: str,
    useridentities_container: str,
    provisioning_container: str,
) -> None:
    """Ensure that the Cosmos DB database and required containers exist.

    This function is intended to be called at application startup
    or during infrastructure initialization.

    Args:
        provider: Cosmos client provider.
        conversations_container: Container name for conversations.
        messages_container: Container name for messages.
        users_container: Container name for users data.
        tenants_container: Container name for tenants data.
        useridentities_container: Container name for user identity data.
        provisioning_container: Container name for provisioning data.
    """
    database = await provider.client.create_database_if_not_exists(id=provider._database_name)

    await database.create_container_if_not_exists(
        id=conversations_container,
        partition_key=PartitionKey(path=CONVERSATIONS_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=messages_container,
        partition_key=PartitionKey(path=MESSAGES_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=users_container,
        partition_key=PartitionKey(path=USERS_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=tenants_container,
        partition_key=PartitionKey(path=TENANTS_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=useridentities_container,
        partition_key=PartitionKey(path=USERIDENTITIES_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=provisioning_container,
        partition_key=PartitionKey(path=PROVISIONING_PARTITION_KEY),
    )
