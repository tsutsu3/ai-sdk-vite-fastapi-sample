from typing import Protocol


class CosmosClientProviderBase(Protocol):
    @property
    def client(self):
        raise NotImplementedError

    def get_container(self, container_name: str):
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class FirestoreClientProviderBase(Protocol):
    async def get_client(self):
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError
