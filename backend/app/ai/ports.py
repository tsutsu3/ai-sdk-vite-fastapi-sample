from typing import Protocol

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever

from app.ai.models import ChatModelSpec, RetrievalPolicy
from app.core.config import AppConfig, ChatCapabilities


class ChatModelBuilder(Protocol):
    def __call__(
        self,
        app_config: AppConfig,
        spec: ChatModelSpec,
        *,
        streaming: bool,
    ) -> BaseChatModel:
        raise NotImplementedError


class ChatModelResolver(Protocol):
    def __call__(
        self,
        chat_caps: ChatCapabilities,
        model_id: str | None,
        *,
        default_model_id: str | None,
    ) -> ChatModelSpec:
        raise NotImplementedError


class RetrieverBuilder(Protocol):
    def __call__(
        self,
        app_config: AppConfig,
        *,
        provider_id: str,
        data_source: str,
        policy: RetrievalPolicy,
        query_embedding: list[float] | None = None,
    ) -> BaseRetriever:
        raise NotImplementedError
