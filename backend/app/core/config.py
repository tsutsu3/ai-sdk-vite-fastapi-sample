from enum import Enum
from typing import Dict, Optional, Set

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevelEnum(str, Enum):
    critical = "CRITICAL"
    error = "ERROR"
    warning = "WARNING"
    info = "INFO"
    debug = "DEBUG"


class StorageBackend(str, Enum):
    memory = "memory"
    azure = "azure"
    gcp = "gcp"
    local = "local"


class AppConfig(BaseModel, frozen=True):
    log_level: LogLevelEnum = LogLevelEnum.info

    # Azure Cosmos DB
    cosmos_endpoint: str = ""
    cosmos_key: str = ""
    cosmos_database: str = "chatdb"
    cosmos_conversations_container: str = "conversations"
    cosmos_messages_container: str = "messages"
    cosmos_usage_container: str = "usage"
    cosmos_authz_container: str = "authz"

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

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Chat title model
    chat_title_model: str = ""

    # Chat model metadata
    chat_model_chefs: Dict[str, str] = Field(default_factory=dict)
    chat_model_chef_slugs: Dict[str, str] = Field(default_factory=dict)
    chat_model_providers: Dict[str, list[str]] = Field(default_factory=dict)

    # Local storage
    local_storage_path: str = ".local-data"

    # Authz cache
    authz_cache_ttl_seconds: int = 3600
    authz_cache_max_size: int = 1000

    # Web search
    web_search_default_engine: str = ""
    web_search_internal_url: str = ""
    web_search_internal_api_key: str = ""
    web_search_internal_auth_header: str = "X-API-Key"
    web_search_fetch_content: bool = False


class StorageCapabilities(BaseModel, frozen=True):
    db_backend: StorageBackend = StorageBackend.memory
    blob_backend: StorageBackend = StorageBackend.memory


ChatProvider = str
ChatModelId = str


class ChatCapabilities(BaseModel, frozen=True):
    providers: Dict[ChatProvider, Set[ChatModelId]] = Field(default_factory=dict)
    model_names: Dict[ChatModelId, str] = Field(default_factory=dict)
    model_chefs: Dict[ChatModelId, str] = Field(default_factory=dict)
    model_chef_slugs: Dict[ChatModelId, str] = Field(default_factory=dict)
    model_providers: Dict[ChatModelId, list[str]] = Field(default_factory=dict)

    def has_provider(self, provider: ChatProvider) -> bool:
        return provider in self.providers

    def has_model(self, provider: ChatProvider, model: ChatModelId) -> bool:
        return model in self.providers.get(provider, set())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    log_level: LogLevelEnum = LogLevelEnum.info

    # Storage capabilities
    db_backend: StorageBackend = StorageBackend.memory
    blob_backend: StorageBackend = StorageBackend.memory

    # Chat capabilities (memory | azure | ollama | gcp)
    chat_providers: Optional[str] = None
    azure_chat_models: Optional[str] = None
    ollama_chat_models: Optional[str] = None
    gcp_chat_models: Optional[str] = None
    chat_model_names: Optional[str] = None
    chat_model_chefs: Optional[str] = None
    chat_model_chef_slugs: Optional[str] = None
    chat_model_providers: Optional[str] = None
    chat_title_model: Optional[str] = None

    # Cosmos DB
    cosmos_endpoint: str = ""
    cosmos_key: str = ""
    cosmos_database: str = "chatdb"
    cosmos_conversations_container: str = "conversations"
    cosmos_messages_container: str = "messages"
    cosmos_usage_container: str = "usage"
    cosmos_authz_container: str = "authz"

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

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Local storage
    local_storage_path: str = ".local-data"

    # Authz cache
    authz_cache_ttl_seconds: int = 3600
    authz_cache_max_size: int = 1000

    # Web search
    web_search_engines: Optional[str] = None
    web_search_default_engine: str = ""
    web_search_internal_url: str = ""
    web_search_internal_api_key: str = ""
    web_search_internal_auth_header: str = "X-API-Key"
    web_search_fetch_content: bool = False

    @property
    def chat_providers_set(self) -> Set[str]:
        if not self.chat_providers:
            return set()
        return {v.strip().lower() for v in self.chat_providers.split(",") if v.strip()}

    @property
    def azure_chat_models_set(self) -> Set[str]:
        if not self.azure_chat_models:
            return set()
        return {v.strip().lower() for v in self.azure_chat_models.split(",") if v.strip()}

    @property
    def gcp_chat_models_set(self) -> Set[str]:
        if not self.gcp_chat_models:
            return set()
        return {v.strip().lower() for v in self.gcp_chat_models.split(",") if v.strip()}

    @property
    def ollama_chat_models_set(self) -> Set[str]:
        if not self.ollama_chat_models:
            return set()
        return {v.strip().lower() for v in self.ollama_chat_models.split(",") if v.strip()}

    @property
    def azure_openai_deployments_dict(self) -> Dict[str, str]:
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
    def web_search_engines_set(self) -> Set[str]:
        if not self.web_search_engines:
            return set()
        return {value.strip().lower() for value in self.web_search_engines.split(",") if value.strip()}

    @model_validator(mode="after")
    def validate_db(self) -> "Settings":
        if self.db_backend == StorageBackend.azure:
            if not (self.cosmos_endpoint and self.cosmos_key and self.cosmos_database):
                raise ValueError("Cosmos settings are required for DB_BACKEND=azure")
        elif self.db_backend == StorageBackend.gcp:
            raise ValueError("GCP backend is not yet supported for DB_BACKEND")
        return self

    @model_validator(mode="after")
    def validate_blob(self) -> "Settings":
        if self.blob_backend == StorageBackend.azure:
            if not self.azure_blob_endpoint or not self.azure_blob_api_key:
                raise ValueError(
                    "AZURE_BLOB_ENDPOINT and AZURE_BLOB_API_KEY are required for BLOB_BACKEND=azure"
                )
        elif self.blob_backend == StorageBackend.gcp:
            raise ValueError("GCP backend is not yet supported for BLOB_BACKEND")
        return self

    @model_validator(mode="after")
    def validate_chat(self) -> "Settings":
        if "azure" in self.chat_providers_set:
            if not (self.azure_openai_endpoint and self.azure_openai_api_key):
                raise ValueError("Azure OpenAI settings are required")
            if not self.azure_chat_models_set:
                raise ValueError("AZURE_CHAT_MODELS must be configured")
            if not self.azure_openai_deployments_dict:
                raise ValueError("AZURE_OPENAI_DEPLOYMENTS must be configured")

        if "gcp" in self.chat_providers_set:
            raise ValueError("GCP chat provider is not yet supported")

        if "ollama" in self.chat_providers_set and not self.ollama_chat_models_set:
            raise ValueError("OLLAMA_CHAT_MODELS must be configured")

        if self.chat_title_model:
            model_id = self.chat_title_model.strip().lower()
            allowed_models = (
                self.azure_chat_models_set
                | self.ollama_chat_models_set
                | self.gcp_chat_models_set
            )
            if model_id and model_id not in allowed_models:
                raise ValueError("CHAT_TITLE_MODEL must be one of the configured chat models")

        return self

    def to_app_config(self) -> AppConfig:
        return AppConfig(
            log_level=self.log_level,
            cosmos_endpoint=self.cosmos_endpoint,
            cosmos_key=self.cosmos_key,
            cosmos_database=self.cosmos_database,
            cosmos_conversations_container=self.cosmos_conversations_container,
            cosmos_messages_container=self.cosmos_messages_container,
            cosmos_usage_container=self.cosmos_usage_container,
            cosmos_authz_container=self.cosmos_authz_container,
            azure_openai_endpoint=self.azure_openai_endpoint,
            azure_openai_api_key=self.azure_openai_api_key,
            azure_openai_api_version=self.azure_openai_api_version,
            azure_openai_deployments=self.azure_openai_deployments_dict,
            azure_openai_title_model=self.azure_openai_title_model,
            chat_title_model=self.chat_title_model or "",
            azure_blob_endpoint=self.azure_blob_endpoint,
            azure_blob_api_key=self.azure_blob_api_key,
            azure_blob_container=self.azure_blob_container,
            gcp_project_id=self.gcp_project_id,
            gcp_location=self.gcp_location,
            ollama_base_url=self.ollama_base_url,
            chat_model_chefs=self.chat_model_chefs_dict,
            chat_model_chef_slugs=self.chat_model_chef_slugs_dict,
            chat_model_providers=self.chat_model_providers_dict,
            local_storage_path=self.local_storage_path,
            authz_cache_ttl_seconds=self.authz_cache_ttl_seconds,
            authz_cache_max_size=self.authz_cache_max_size,
            web_search_default_engine=self.web_search_default_engine or "",
            web_search_internal_url=self.web_search_internal_url,
            web_search_internal_api_key=self.web_search_internal_api_key,
            web_search_internal_auth_header=self.web_search_internal_auth_header,
            web_search_fetch_content=self.web_search_fetch_content,
        )

    def to_storage_capabilities(self) -> StorageCapabilities:
        return StorageCapabilities(
            db_backend=self.db_backend,
            blob_backend=self.blob_backend,
        )

    def to_chat_capabilities(self) -> ChatCapabilities:
        providers: Dict[str, Set[str]] = {}

        if "memory" in self.chat_providers_set:
            providers["memory"] = {"dummy"}

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
