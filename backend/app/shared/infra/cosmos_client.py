from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient, ContainerProxy

from app.core.config import AppConfig

CONVERSATIONS_PARTITION_KEY = "/tenantId/userId"
MESSAGES_PARTITION_KEY = "/tenantId/convId"
USAGE_PARTITION_KEY = "/tenantId/userId"
AUTHZ_PARTITION_KEY = "/tenantId/userId"


def get_cosmos_client(config: AppConfig) -> CosmosClient:
    if not config.cosmos_endpoint or not config.cosmos_key:
        raise RuntimeError("COSMOS_ENDPOINT or COSMOS_KEY is not configured.")
    return CosmosClient(config.cosmos_endpoint, credential=config.cosmos_key)


async def ensure_cosmos_resources(config: AppConfig) -> None:
    client = get_cosmos_client(config)
    database = await client.create_database_if_not_exists(id=config.cosmos_database)
    await database.create_container_if_not_exists(
        id=config.cosmos_conversations_container,
        partition_key=PartitionKey(path=CONVERSATIONS_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=config.cosmos_messages_container,
        partition_key=PartitionKey(path=MESSAGES_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=config.cosmos_usage_container,
        partition_key=PartitionKey(path=USAGE_PARTITION_KEY),
    )
    await database.create_container_if_not_exists(
        id=config.cosmos_authz_container,
        partition_key=PartitionKey(path=AUTHZ_PARTITION_KEY),
    )


def get_cosmos_container(config: AppConfig, container_name: str) -> ContainerProxy:
    client = get_cosmos_client(config)
    database = client.get_database_client(config.cosmos_database)
    return database.get_container_client(container_name)
