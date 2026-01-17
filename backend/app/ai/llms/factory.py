from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from app.ai.llms.fake_chat_model import FakeChatModel
from app.ai.models import ChatModelSpec, EmbeddingSpec
from app.core.config import AppConfig, ChatCapabilities


def build_chat_model(
    app_config: AppConfig, spec: ChatModelSpec, *, streaming: bool
) -> BaseChatModel:
    if spec.provider == "fake":
        delay_ms = app_config.chat_fake_stream_delay_ms
        return _build_fake_chat_model(spec.model_id, delay_ms / 1000 if delay_ms else 0.0)
    if spec.provider == "azure":
        return _build_azure_chat_model(app_config, spec, streaming=streaming)
    if spec.provider == "gcp":
        return _build_gcp_chat_model(app_config, spec, streaming=streaming)
    raise RuntimeError(f"Unsupported chat provider: {spec.provider}")


def build_embeddings(app_config: AppConfig, spec: EmbeddingSpec) -> Embeddings:
    if spec.provider == "azure":
        return _build_azure_embeddings(app_config, spec)
    if spec.provider == "gcp":
        return _build_gcp_embeddings(app_config, spec)
    raise RuntimeError(f"Unsupported embeddings provider: {spec.provider}")


def resolve_chat_model(
    chat_caps: ChatCapabilities,
    model_id: str | None,
    *,
    default_model_id: str | None,
) -> ChatModelSpec:
    selected = model_id or default_model_id
    if not selected:
        raise RuntimeError("Model must be specified.")
    for provider, models in chat_caps.providers.items():
        if selected in models:
            return ChatModelSpec(provider=provider, model_id=selected)
    raise RuntimeError("Requested model is not available.")


def _build_fake_chat_model(model_id: str, stream_delay_seconds: float = 0.0) -> BaseChatModel:
    return FakeChatModel(model_id, stream_delay_seconds=stream_delay_seconds)


def _build_azure_chat_model(
    app_config: AppConfig, spec: ChatModelSpec, *, streaming: bool
) -> BaseChatModel:
    deployment = app_config.azure_openai_deployments.get(spec.model_id, "")
    if not deployment:
        raise RuntimeError("Azure OpenAI deployment is not configured.")
    return AzureChatOpenAI(
        api_key=app_config.azure_openai_api_key,
        api_version=app_config.azure_openai_api_version,
        azure_endpoint=app_config.azure_openai_endpoint,
        azure_deployment=deployment,
        streaming=streaming,
    )


def _build_gcp_chat_model(
    app_config: AppConfig, spec: ChatModelSpec, *, streaming: bool
) -> BaseChatModel:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise RuntimeError("langchain-google-genai is required for GCP chat.") from exc
    return ChatGoogleGenerativeAI(
        model=spec.model_id,
        api_key=app_config.google_api_key or None,
        streaming=streaming,
    )


def _build_azure_embeddings(app_config: AppConfig, spec: EmbeddingSpec) -> Embeddings:
    deployment = app_config.azure_openai_deployments.get(spec.model_id, "")
    if not deployment:
        raise RuntimeError("Azure OpenAI deployment is not configured.")
    return AzureOpenAIEmbeddings(
        api_key=app_config.azure_openai_api_key,
        api_version=app_config.azure_openai_api_version,
        azure_endpoint=app_config.azure_openai_endpoint,
        azure_deployment=deployment,
    )


def _build_gcp_embeddings(app_config: AppConfig, spec: EmbeddingSpec) -> Embeddings:
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
    except ImportError as exc:
        raise RuntimeError("langchain-google-genai is required for GCP embeddings.") from exc
    return GoogleGenerativeAIEmbeddings(
        model=spec.model_id,
        google_api_key=app_config.google_api_key or None,
    )
