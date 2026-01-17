"""Application configuration and settings.

This module parses environment variables (including `.env` files) using
pydantic-settings and converts them into validated, strongly-typed
configuration objects.

Priority order (highest → lowest):
1. OS environment variables
2. backend/.env
3. .env
"""

import os
from enum import Enum
from typing import Dict, Optional, Set

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevelEnum(str, Enum):
    """Log level enum for application logging."""

    critical = "CRITICAL"
    error = "ERROR"
    warning = "WARNING"
    info = "INFO"
    debug = "DEBUG"


class LogFormat(str, Enum):
    """Log format enum for application logging."""

    json = "json"
    text = "text"


class StorageBackend(str, Enum):
    """Supported storage backends."""

    memory = "memory"
    azure = "azure"
    gcp = "gcp"
    local = "local"


class UsageBufferBackend(str, Enum):
    """Usage buffer storage backends for raw logs."""

    off = "off"
    local = "local"
    azure = "azure"
    gcp = "gcp"


class AuthProvider(str, Enum):
    """Supported authentication providers."""

    iap = "iap"
    easyauth = "easyauth"
    local = "local"
    none = "none"


class CacheBackend(str, Enum):
    """Supported cache backends."""

    memory = "memory"
    redis = "redis"
    off = "off"


class OpenTelemetryExporter(str, Enum):
    """Supported OpenTelemetry exporters."""

    console = "console"
    otlp = "otlp"
    azure = "azure"


class AppConfig(BaseModel):
    """Resolved application configuration values."""

    model_config = ConfigDict(frozen=True)

    log_level: LogLevelEnum = LogLevelEnum.info
    log_format: LogFormat = LogFormat.json
    app_env: str = "local"

    # Azure Cosmos DB
    cosmos_endpoint: str = ""
    cosmos_key: str = ""
    database: str = "chatdb"

    # Database containers/collections (shared by Cosmos DB and Firestore)
    conversations_container: str = "conversations"
    messages_container: str = "messages"
    users_container: str = "users"
    tenants_container: str = "tenants"
    useridentities_container: str = "useridentities"
    provisioning_container: str = "provisioning"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_deployments: Dict[str, str] = Field(default_factory=dict)
    azure_openai_title_model: str = ""

    # Azure Blob
    azure_blob_endpoint: str = ""
    azure_blob_api_key: str = ""
    azure_blob_container: str = "attachments"

    # GCP
    gcp_project_id: str = ""
    gcp_location: str = ""
    gcs_bucket: str = ""
    gcs_prefix: str = "uploads"
    google_api_key: str = ""
    embeddings_provider: str = ""
    embeddings_model: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Chat title model
    chat_title_model: str = ""
    chat_default_model: str = ""

    # Chat model metadata
    chat_model_chefs: Dict[str, str] = Field(default_factory=dict)
    chat_model_chef_slugs: Dict[str, str] = Field(default_factory=dict)
    chat_model_providers: Dict[str, list[str]] = Field(default_factory=dict)

    # Local storage
    local_storage_path: str = ".local-data"
    blob_object_url_ttl_seconds: int = 1 * 60

    # Cache configuration
    cache_backend: CacheBackend = CacheBackend.memory

    # Authz cache settings
    authz_cache_ttl_seconds: int = 3600
    authz_cache_max_size: int = 1000
    authz_redis_db: int = 0

    # Message cache settings
    messages_cache_ttl_seconds: int = 15 * 60
    messages_cache_max_size: int = 100
    messages_cache_max_bytes: int = 5 * 1024 * 1024
    messages_redis_db: int = 1

    # Redis connection (shared by authz and messages)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_ssl: bool = False

    # Deprecated settings (for backwards compatibility)
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000

    # Usage buffer
    usage_buffer_backend: UsageBufferBackend = UsageBufferBackend.local
    usage_buffer_local_path: str = ".local-data/usage-buffer"
    usage_buffer_flush_max_records: int = 100
    usage_buffer_flush_interval_seconds: int = 60
    usage_buffer_blob_container: str = "usage-raw"
    usage_buffer_blob_prefix: str = "usage/raw"
    usage_buffer_gcs_bucket: str = ""
    usage_buffer_gcs_prefix: str = "usage/raw"

    # Pagination defaults and max limits
    messages_page_default_limit: int = 30
    messages_page_max_limit: int = 200
    conversations_page_default_limit: int = 50
    conversations_page_max_limit: int = 200

    # CORS
    cors_allowed_origins: list[str] = Field(default_factory=list)

    # File upload limits
    file_upload_max_bytes: int = 10 * 1024 * 1024  # 10 MB
    file_upload_allowed_types: list[str] = Field(default_factory=list)

    # RAG
    retrieval_ai_search_url: str = ""
    retrieval_ai_search_api_key: str = ""
    retrieval_ai_search_auth_header: str = "X-API-Key"
    retrieval_local_path: str = "backend/app/infra/fixtures/retrieval"
    retrieval_tools_config_path: str = "retrieval_tools.yaml"
    vertex_search_project_id: str = ""
    vertex_search_location: str = "global"
    vertex_search_collection: str = "default_collection"
    vertex_search_data_store: str = ""
    vertex_search_serving_config: str = "default_search"
    vertex_search_filter_template: str = ""

    # Auth provider
    auth_provider: AuthProvider = AuthProvider.local

    # Local auth user info
    local_auth_user_id: str = "local-user-001"
    local_auth_user_email: EmailStr = "local.user001@example.com"

    # OpenTelemetry
    otel_enabled: bool = False
    otel_service_name: str = "ai-sdk-vite-fastapi-sample-backend"
    otel_exporter: OpenTelemetryExporter = OpenTelemetryExporter.console
    otel_exporter_otlp_protocol: str = "grpc"
    otel_exporter_otlp_endpoint: str = ""
    azure_monitor_connection_string: str = ""

    # Streaming
    stream_idle_timeout_seconds: int = 300


class StorageCapabilities(BaseModel):
    """Storage backend capabilities used by the application."""

    model_config = ConfigDict(frozen=True)

    db_backend: StorageBackend = StorageBackend.memory
    blob_backend: StorageBackend = StorageBackend.memory


ChatProvider = str
ChatModelId = str


class ChatCapabilities(BaseModel):
    """Derived chat provider capabilities and metadata."""

    model_config = ConfigDict(frozen=True)

    providers: Dict[ChatProvider, Set[ChatModelId]] = Field(default_factory=dict)
    model_names: Dict[ChatModelId, str] = Field(default_factory=dict)
    model_chefs: Dict[ChatModelId, str] = Field(default_factory=dict)
    model_chef_slugs: Dict[ChatModelId, str] = Field(default_factory=dict)
    model_providers: Dict[ChatModelId, list[str]] = Field(default_factory=dict)

    def has_provider(self, provider: ChatProvider) -> bool:
        """Check if a provider is enabled.

        Args:
            provider: Provider id.

        Returns:
            bool: True if enabled.
        """
        return provider in self.providers

    def has_model(self, provider: ChatProvider, model: ChatModelId) -> bool:
        """Check if a model is enabled for a provider.

        Args:
            provider: Provider id.
            model: Model id.

        Returns:
            bool: True if enabled.
        """
        return model in self.providers.get(provider, set())


class Settings(BaseSettings):
    """Settings loader and validators for environment configuration."""

    _env_name = (os.getenv("APP_ENV") or "").strip()
    if _env_name:
        _env_file = (f".env.{_env_name}",)
    else:
        _env_file = (".env",)

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        # extra="ignore",
    )

    log_level: LogLevelEnum = LogLevelEnum.info
    log_format: LogFormat = LogFormat.json
    app_env: str = "local"

    # Storage capabilities
    db_backend: StorageBackend = StorageBackend.memory
    blob_backend: StorageBackend = StorageBackend.memory

    # Chat capabilities (fake | azure | ollama | gcp)
    chat_providers: Optional[str] = "fake"
    chat_fake_models: Optional[str] = "fake-static,fake-random"
    azure_chat_models: Optional[str] = None
    ollama_chat_models: Optional[str] = None
    gcp_chat_models: Optional[str] = None
    chat_model_names: Optional[str] = None
    chat_model_chefs: Optional[str] = None
    chat_model_chef_slugs: Optional[str] = None
    chat_model_providers: Optional[str] = None
    chat_title_model: Optional[str] = None
    chat_default_model: Optional[str] = None

    # Cosmos DB
    cosmos_endpoint: str = ""
    cosmos_key: str = ""
    database: str = "chatdb"

    # Database containers/collections (shared by Cosmos DB and Firestore)
    conversations_container: str = "conversations"
    messages_container: str = "messages"
    users_container: str = "users"
    tenants_container: str = "tenants"
    useridentities_container: str = "useridentities"
    provisioning_container: str = "provisioning"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_deployments: Optional[str] = None
    azure_openai_title_model: str = ""

    # Azure Blob
    azure_blob_endpoint: str = ""
    azure_blob_api_key: str = ""
    azure_blob_container: str = "attachments"

    # GCP
    gcp_project_id: str = ""
    gcp_location: str = ""
    gcs_bucket: str = ""
    gcs_prefix: str = "uploads"
    google_api_key: str = ""
    embeddings_provider: str = ""
    embeddings_model: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Local storage
    local_storage_path: str = ".local-data"
    blob_object_url_ttl_seconds: int = 15 * 60

    # Cache configuration
    cache_backend: CacheBackend = CacheBackend.memory

    # Authz cache
    authz_cache_ttl_seconds: int = 3600
    authz_cache_max_size: int = 1000
    authz_redis_db: int = 0

    # Message cache
    messages_cache_ttl_seconds: int = 15 * 60
    messages_cache_max_size: int = 100
    messages_cache_max_bytes: int = 5 * 1024 * 1024
    messages_redis_db: int = 1

    # Redis connection (shared by authz and messages)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_ssl: bool = False

    # Usage buffer
    usage_buffer_backend: UsageBufferBackend = UsageBufferBackend.local
    usage_buffer_local_path: str = ".local-data/usage-buffer"
    usage_buffer_flush_max_records: int = 100
    usage_buffer_flush_interval_seconds: int = 60
    usage_buffer_blob_container: str = "usage-raw"
    usage_buffer_blob_prefix: str = "usage/raw"
    usage_buffer_gcs_bucket: str = ""
    usage_buffer_gcs_prefix: str = "usage/raw"

    # Pagination defaults and max limits
    messages_page_default_limit: int = 30
    messages_page_max_limit: int = 200
    conversations_page_default_limit: int = 50
    conversations_page_max_limit: int = 200

    # CORS
    cors_allowed_origins: str = ""

    # File upload limits
    file_upload_max_bytes: int = 10 * 1024 * 1024
    file_upload_allowed_types: str = ""

    # RAG
    retrieval_ai_search_url: str = ""
    retrieval_ai_search_api_key: str = ""
    retrieval_ai_search_auth_header: str = "X-API-Key"
    retrieval_local_path: str = "backend/app/infra/fixtures/retrieval"
    retrieval_tools_config_path: str = "retrieval_tools.yaml"
    vertex_search_project_id: str = ""
    vertex_search_location: str = "global"
    vertex_search_collection: str = "default_collection"
    vertex_search_data_store: str = ""
    vertex_search_serving_config: str = "default_search"

    # Auth provider
    auth_provider: AuthProvider = AuthProvider.local

    # Local auth user info
    local_auth_user_id: str = "local-user-001"
    local_auth_user_email: EmailStr = "local.user001@example.com"

    # OpenTelemetry
    otel_enabled: bool = False
    otel_service_name: str = "ai-sdk-fastapi-chat-backend"
    otel_exporter: OpenTelemetryExporter = OpenTelemetryExporter.console
    otel_exporter_otlp_protocol: str = "grpc"
    otel_exporter_otlp_endpoint: str = ""
    azure_monitor_connection_string: str = ""

    # Streaming
    stream_idle_timeout_seconds: int = 300

    vertex_search_filter_template: str = ""

    @property
    def chat_providers_set(self) -> Set[str]:
        """Parse the configured chat providers into a set.

        Returns:
            Set[str]: Provider ids.
        """
        if not self.chat_providers:
            return set()
        return {v.strip().lower() for v in self.chat_providers.split(",") if v.strip()}

    @property
    def azure_chat_models_set(self) -> Set[str]:
        """Parse Azure chat models into a set.

        Returns:
            Set[str]: Model ids.
        """
        if not self.azure_chat_models:
            return set()
        return {v.strip().lower() for v in self.azure_chat_models.split(",") if v.strip()}

    @property
    def fake_chat_models_set(self) -> Set[str]:
        """Parse fake chat models into a set.

        Returns:
            Set[str]: Model ids.
        """
        if not self.chat_fake_models:
            return set()
        return {v.strip().lower() for v in self.chat_fake_models.split(",") if v.strip()}

    @property
    def gcp_chat_models_set(self) -> Set[str]:
        """Parse GCP chat models into a set.

        Returns:
            Set[str]: Model ids.
        """
        if not self.gcp_chat_models:
            return set()
        return {v.strip().lower() for v in self.gcp_chat_models.split(",") if v.strip()}

    @property
    def ollama_chat_models_set(self) -> Set[str]:
        """Parse Ollama chat models into a set.

        Returns:
            Set[str]: Model ids.
        """
        if not self.ollama_chat_models:
            return set()
        return {v.strip().lower() for v in self.ollama_chat_models.split(",") if v.strip()}

    @property
    def azure_openai_deployments_dict(self) -> Dict[str, str]:
        """Parse Azure OpenAI deployment mappings into a dict.

        Returns:
            Dict[str, str]: Model-to-deployment mapping.
        """
        if not self.azure_openai_deployments:
            return {}

        deployments: Dict[str, str] = {}
        for pair in self.azure_openai_deployments.split(","):
            if "=" not in pair:
                raise ValueError("AZURE_OPENAI_DEPLOYMENTS must be 'model=deployment,...'")
            model, deployment = pair.split("=", 1)
            deployments[model.strip()] = deployment.strip()
        return deployments

    @property
    def chat_model_names_dict(self) -> Dict[str, str]:
        """Parse chat model display names into a dict.

        Returns:
            Dict[str, str]: Model-to-name mapping.
        """
        if not self.chat_model_names:
            return {}
        names: Dict[str, str] = {}
        for pair in self.chat_model_names.split(","):
            if "=" not in pair:
                raise ValueError("CHAT_MODEL_NAMES must be 'model=name,...'")
            model, name = pair.split("=", 1)
            names[model.strip().lower()] = name.strip()
        return names

    @property
    def chat_model_chefs_dict(self) -> Dict[str, str]:
        """Parse chat model chef labels into a dict.

        Returns:
            Dict[str, str]: Model-to-chef mapping.
        """
        if not self.chat_model_chefs:
            return {}
        chefs: Dict[str, str] = {}
        for pair in self.chat_model_chefs.split(","):
            if "=" not in pair:
                raise ValueError("CHAT_MODEL_CHEFS must be 'model=chef,...'")
            model, chef = pair.split("=", 1)
            chefs[model.strip().lower()] = chef.strip()
        return chefs

    @property
    def chat_model_chef_slugs_dict(self) -> Dict[str, str]:
        """Parse chat model chef slugs into a dict.

        Returns:
            Dict[str, str]: Model-to-chef slug mapping.
        """
        if not self.chat_model_chef_slugs:
            return {}
        slugs: Dict[str, str] = {}
        for pair in self.chat_model_chef_slugs.split(","):
            if "=" not in pair:
                raise ValueError("CHAT_MODEL_CHEF_SLUGS must be 'model=slug,...'")
            model, slug = pair.split("=", 1)
            slugs[model.strip().lower()] = slug.strip().lower()
        return slugs

    @property
    def chat_model_providers_dict(self) -> Dict[str, list[str]]:
        """Parse chat model provider lists into a dict.

        Returns:
            Dict[str, list[str]]: Model-to-provider list mapping.
        """
        if not self.chat_model_providers:
            return {}
        providers: Dict[str, list[str]] = {}
        for pair in self.chat_model_providers.split(","):
            if "=" not in pair:
                raise ValueError("CHAT_MODEL_PROVIDERS must be 'model=provider|provider,...'")
            model, provider_list = pair.split("=", 1)
            items = [value.strip().lower() for value in provider_list.split("|") if value.strip()]
            providers[model.strip().lower()] = items
        return providers

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        if not self.cors_allowed_origins:
            return []
        return [v.strip() for v in self.cors_allowed_origins.split(",") if v.strip()]

    @property
    def file_upload_allowed_types_list(self) -> list[str]:
        if not self.file_upload_allowed_types:
            return []
        return [v.strip() for v in self.file_upload_allowed_types.split(",") if v.strip()]

    @model_validator(mode="after")
    def validate_db(self) -> "Settings":
        """Validate database backend settings.

        Returns:
            Settings: Validated settings.
        """
        if self.db_backend == StorageBackend.azure:
            if not (self.cosmos_endpoint and self.cosmos_key and self.database):
                raise ValueError("Cosmos settings are required for DB_BACKEND=azure")
        elif self.db_backend == StorageBackend.gcp:
            if not self.gcp_project_id:
                raise ValueError("GCP_PROJECT_ID is required for DB_BACKEND=gcp")
        return self

    @model_validator(mode="after")
    def validate_blob(self) -> "Settings":
        """Validate blob storage backend settings.

        Returns:
            Settings: Validated settings.
        """
        if self.blob_backend == StorageBackend.azure:
            if not self.azure_blob_endpoint or not self.azure_blob_api_key:
                raise ValueError(
                    "AZURE_BLOB_ENDPOINT and AZURE_BLOB_API_KEY are required for BLOB_BACKEND=azure"
                )
        elif self.blob_backend == StorageBackend.gcp:
            if not self.gcp_project_id:
                raise ValueError("GCP_PROJECT_ID is required for BLOB_BACKEND=gcp")
            if not self.gcs_bucket:
                raise ValueError("GCS_BUCKET is required for BLOB_BACKEND=gcp")
        return self

    @model_validator(mode="after")
    def validate_chat(self) -> "Settings":
        """Validate chat provider settings.

        Returns:
            Settings: Validated settings.
        """
        if "fake" in self.chat_providers_set and not self.fake_chat_models_set:
            raise ValueError("CHAT_FAKE_MODELS must be configured")

        if "azure" in self.chat_providers_set:
            if not (self.azure_openai_endpoint and self.azure_openai_api_key):
                raise ValueError("Azure OpenAI settings are required")
            if not self.azure_chat_models_set:
                raise ValueError("AZURE_CHAT_MODELS must be configured")
            if not self.azure_openai_deployments_dict:
                raise ValueError("AZURE_OPENAI_DEPLOYMENTS must be configured")

        if "gcp" in self.chat_providers_set:
            if not self.google_api_key:
                raise ValueError("GOOGLE_API_KEY is required for GCP chat")
            if not self.gcp_chat_models_set:
                raise ValueError("GCP_CHAT_MODELS must be configured")

        if "ollama" in self.chat_providers_set and not self.ollama_chat_models_set:
            raise ValueError("OLLAMA_CHAT_MODELS must be configured")

        if self.chat_title_model:
            model_id = self.chat_title_model.strip().lower()
            allowed_models = (
                self.fake_chat_models_set
                | self.azure_chat_models_set
                | self.ollama_chat_models_set
                | self.gcp_chat_models_set
            )
            if model_id and model_id not in allowed_models:
                raise ValueError("CHAT_TITLE_MODEL must be one of the configured chat models")

        if self.chat_default_model:
            model_id = self.chat_default_model.strip().lower()
            allowed_models = (
                self.fake_chat_models_set
                | self.azure_chat_models_set
                | self.ollama_chat_models_set
                | self.gcp_chat_models_set
            )
            if model_id and model_id not in allowed_models:
                raise ValueError("CHAT_DEFAULT_MODEL must be one of the configured chat models")

        return self

    # @model_validator(mode="after")
    # def validate_auth_provider(self) -> "Settings":
    #     env = (self.app_env or "").strip().lower()
    #     if env in {"prod", "production"} and self.auth_provider in {
    #         AuthProvider.local,
    #         AuthProvider.none,
    #     }:
    #         raise ValueError("AUTH_PROVIDER cannot be local/none in production")
    #     return self

    @model_validator(mode="after")
    def validate_pagination(self) -> "Settings":
        """Validate pagination defaults and limits.

        Returns:
            Settings: Validated settings.
        """
        if self.messages_page_default_limit <= 0:
            raise ValueError("MESSAGES_PAGE_DEFAULT_LIMIT must be > 0")
        if self.messages_page_max_limit <= 0:
            raise ValueError("MESSAGES_PAGE_MAX_LIMIT must be > 0")
        if self.messages_page_default_limit > self.messages_page_max_limit:
            raise ValueError("MESSAGES_PAGE_DEFAULT_LIMIT must be <= MESSAGES_PAGE_MAX_LIMIT")

        if self.conversations_page_default_limit <= 0:
            raise ValueError("CONVERSATIONS_PAGE_DEFAULT_LIMIT must be > 0")
        if self.conversations_page_max_limit <= 0:
            raise ValueError("CONVERSATIONS_PAGE_MAX_LIMIT must be > 0")
        if self.conversations_page_default_limit > self.conversations_page_max_limit:
            raise ValueError(
                "CONVERSATIONS_PAGE_DEFAULT_LIMIT must be <= CONVERSATIONS_PAGE_MAX_LIMIT"
            )

        return self

    def to_app_config(self) -> AppConfig:
        """Convert settings into immutable application config.

        Returns:
            AppConfig: Application configuration.
        """
        return AppConfig(
            log_level=self.log_level,
            log_format=self.log_format,
            app_env=self.app_env,
            cosmos_endpoint=self.cosmos_endpoint,
            cosmos_key=self.cosmos_key,
            database=self.database,
            conversations_container=self.conversations_container,
            messages_container=self.messages_container,
            users_container=self.users_container,
            tenants_container=self.tenants_container,
            useridentities_container=self.useridentities_container,
            provisioning_container=self.provisioning_container,
            azure_openai_endpoint=self.azure_openai_endpoint,
            azure_openai_api_key=self.azure_openai_api_key,
            azure_openai_api_version=self.azure_openai_api_version,
            azure_openai_deployments=self.azure_openai_deployments_dict,
            azure_openai_title_model=self.azure_openai_title_model,
            chat_title_model=self.chat_title_model or "",
            chat_default_model=(self.chat_default_model or "").strip().lower(),
            azure_blob_endpoint=self.azure_blob_endpoint,
            azure_blob_api_key=self.azure_blob_api_key,
            azure_blob_container=self.azure_blob_container,
            gcp_project_id=self.gcp_project_id,
            gcp_location=self.gcp_location,
            gcs_bucket=self.gcs_bucket,
            gcs_prefix=self.gcs_prefix,
            google_api_key=self.google_api_key,
            embeddings_provider=self.embeddings_provider,
            embeddings_model=self.embeddings_model,
            ollama_base_url=self.ollama_base_url,
            chat_model_chefs=self.chat_model_chefs_dict,
            chat_model_chef_slugs=self.chat_model_chef_slugs_dict,
            chat_model_providers=self.chat_model_providers_dict,
            local_storage_path=self.local_storage_path,
            blob_object_url_ttl_seconds=self.blob_object_url_ttl_seconds,
            cache_backend=self.cache_backend,
            authz_cache_ttl_seconds=self.authz_cache_ttl_seconds,
            authz_cache_max_size=self.authz_cache_max_size,
            authz_redis_db=self.authz_redis_db,
            messages_cache_ttl_seconds=self.messages_cache_ttl_seconds,
            messages_cache_max_size=self.messages_cache_max_size,
            messages_cache_max_bytes=self.messages_cache_max_bytes,
            messages_redis_db=self.messages_redis_db,
            redis_host=self.redis_host,
            redis_port=self.redis_port,
            redis_password=self.redis_password,
            redis_ssl=self.redis_ssl,
            usage_buffer_backend=self.usage_buffer_backend,
            usage_buffer_local_path=self.usage_buffer_local_path,
            usage_buffer_flush_max_records=self.usage_buffer_flush_max_records,
            usage_buffer_flush_interval_seconds=self.usage_buffer_flush_interval_seconds,
            usage_buffer_blob_container=self.usage_buffer_blob_container,
            usage_buffer_blob_prefix=self.usage_buffer_blob_prefix,
            usage_buffer_gcs_bucket=self.usage_buffer_gcs_bucket,
            usage_buffer_gcs_prefix=self.usage_buffer_gcs_prefix,
            messages_page_default_limit=self.messages_page_default_limit,
            messages_page_max_limit=self.messages_page_max_limit,
            conversations_page_default_limit=self.conversations_page_default_limit,
            conversations_page_max_limit=self.conversations_page_max_limit,
            cors_allowed_origins=self.cors_allowed_origins_list,
            file_upload_max_bytes=self.file_upload_max_bytes,
            file_upload_allowed_types=self.file_upload_allowed_types_list,
            retrieval_ai_search_url=self.retrieval_ai_search_url,
            retrieval_ai_search_api_key=self.retrieval_ai_search_api_key,
            retrieval_ai_search_auth_header=self.retrieval_ai_search_auth_header,
            retrieval_local_path=self.retrieval_local_path,
            retrieval_tools_config_path=self.retrieval_tools_config_path,
            vertex_search_project_id=self.vertex_search_project_id or self.gcp_project_id,
            vertex_search_location=self.vertex_search_location or "global",
            vertex_search_collection=self.vertex_search_collection or "default_collection",
            vertex_search_data_store=self.vertex_search_data_store,
            vertex_search_serving_config=(self.vertex_search_serving_config or "default_search"),
            vertex_search_filter_template=self.vertex_search_filter_template,
            auth_provider=self.auth_provider,
            local_auth_user_id=self.local_auth_user_id,
            local_auth_user_email=self.local_auth_user_email,
            otel_enabled=self.otel_enabled,
            otel_service_name=self.otel_service_name,
            otel_exporter=self.otel_exporter,
            otel_exporter_otlp_protocol=self.otel_exporter_otlp_protocol,
            otel_exporter_otlp_endpoint=self.otel_exporter_otlp_endpoint,
            azure_monitor_connection_string=self.azure_monitor_connection_string,
            stream_idle_timeout_seconds=self.stream_idle_timeout_seconds,
        )

    def to_storage_capabilities(self) -> StorageCapabilities:
        """Convert settings into storage capabilities.

        Returns:
            StorageCapabilities: Storage capability configuration.
        """
        return StorageCapabilities(
            db_backend=self.db_backend,
            blob_backend=self.blob_backend,
        )

    def to_chat_capabilities(self) -> ChatCapabilities:
        """Convert settings into chat capabilities.

        Returns:
            ChatCapabilities: Chat capability configuration.
        """
        providers: Dict[str, Set[str]] = {}

        if "fake" in self.chat_providers_set:
            providers["fake"] = self.fake_chat_models_set

        if "azure" in self.chat_providers_set:
            providers["azure"] = self.azure_chat_models_set

        if "ollama" in self.chat_providers_set:
            providers["ollama"] = self.ollama_chat_models_set

        if "gcp" in self.chat_providers_set:
            providers["gcp"] = self.gcp_chat_models_set

        return ChatCapabilities(
            providers=providers,
            model_names=self.chat_model_names_dict,
            model_chefs=self.chat_model_chefs_dict,
            model_chef_slugs=self.chat_model_chef_slugs_dict,
            model_providers=self.chat_model_providers_dict,
        )
