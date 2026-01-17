from google.cloud import firestore

from app.core.config import AppConfig


class FirestoreClientProvider:
    """Provides access to a Firestore client.

    This class is responsible for:
    - Creating and holding a Firestore AsyncClient instance
    - Managing client lifecycle (initialization and cleanup)

    It does NOT create collections or documents.
    Resource provisioning should be handled separately.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize the Firestore client provider.

        Args:
            config: Application configuration containing GCP settings.
        """
        self._config = config
        self._client: firestore.AsyncClient | None = None

    def __str__(self) -> str:
        return f"FirestoreClientProvider(project={self._config.gcp_project_id}, database={self._config.database})"

    async def get_client(self) -> firestore.AsyncClient:
        """Get or create the Firestore AsyncClient instance.

        Returns:
            firestore.AsyncClient: The Firestore async client.
        """
        if self._client is None:
            self._client = firestore.AsyncClient(
                project=self._config.gcp_project_id, database=self._config.database
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying Firestore client."""
        if self._client is not None:
            self._client.close()
            self._client = None
