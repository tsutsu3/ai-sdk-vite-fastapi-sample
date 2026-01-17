from collections.abc import AsyncIterator
from logging import getLogger

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI

from app.core.config import AppConfig, ChatCapabilities
from app.features.chat.run.streamers.base import BaseStreamer
from app.features.messages.models import MessageRecord
from app.features.title.utils import generate_fallback_title

logger = getLogger(__name__)


class LangChainChatStreamer(BaseStreamer):
    """Unified LangChain-based streamer for chat providers."""

    def __init__(self, config: AppConfig, chat_caps: ChatCapabilities) -> None:
        super().__init__()
        self._config = config
        self._providers = chat_caps.providers
        self._model_to_provider: dict[str, str] = {}
        for provider, models in self._providers.items():
            for model_id in models:
                if model_id in self._model_to_provider:
                    raise RuntimeError(
                        f"Model '{model_id}' is configured for multiple providers."
                    )
                self._model_to_provider[model_id] = provider
        self._default_model_id = self._resolve_default_model_id()

    def _resolve_default_model_id(self) -> str | None:
        model_id = self._config.chat_default_model
        if model_id in self._model_to_provider:
            return model_id
        if len(self._model_to_provider) == 1:
            return next(iter(self._model_to_provider))
        return None

    def _resolve_provider(self, model_id: str | None) -> tuple[str, str]:
        resolved_model = model_id or self._default_model_id
        if not resolved_model:
            raise RuntimeError("Model must be specified.")
        provider = self._model_to_provider.get(resolved_model)
        if not provider:
            raise RuntimeError("Requested model is not available.")
        return provider, resolved_model

    def _resolve_azure_deployment(self, model_id: str) -> str:
        deployments = self._config.azure_openai_deployments
        if not deployments:
            raise RuntimeError("Azure OpenAI deployments are not configured.")
        deployment = deployments.get(model_id)
        if not deployment:
            raise RuntimeError("Requested model is not available.")
        return deployment

    def _build_llm(self, provider: str, model_id: str, *, streaming: bool):
        if provider == "fake":
            from app.ai.llms.factory import build_chat_model
            from app.ai.models import ChatModelSpec

            return build_chat_model(
                self._config,
                ChatModelSpec(provider="fake", model_id=model_id),
                streaming=streaming,
            )
        if provider == "azure":
            deployment = self._resolve_azure_deployment(model_id)
            return AzureChatOpenAI(
                api_key=self._config.azure_openai_api_key,
                api_version=self._config.azure_openai_api_version,
                azure_endpoint=self._config.azure_openai_endpoint,
                azure_deployment=deployment,
                streaming=streaming,
            )
        if provider == "ollama":
            return ChatOllama(
                model=model_id,
                base_url=self._config.ollama_base_url.rstrip("/"),
                streaming=streaming,
            )
        if provider == "gcp":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as exc:
                raise RuntimeError(
                    "langchain-google-genai is required for GCP chat provider."
                ) from exc
            return ChatGoogleGenerativeAI(
                model=model_id,
                api_key=self._config.google_api_key or None,
                streaming=streaming,
            )
        return None

    @staticmethod
    def _extract_delta(chunk: BaseMessage | AIMessageChunk) -> str:
        content = getattr(chunk, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            return "".join(text_parts)
        return ""

    async def stream_chat(
        self,
        messages: list[BaseMessage],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        provider, resolved_model = self._resolve_provider(model_id)
        logger.info("chat.stream.start provider=%s model_id=%s", provider, resolved_model)
        llm = self._build_llm(provider, resolved_model, streaming=True)
        if llm is None:
            raise RuntimeError("Requested model is not available.")
        prompt = ChatPromptTemplate.from_messages([MessagesPlaceholder("messages")])
        chain = prompt | llm
        async for chunk in chain.astream({"messages": messages}):
            delta = self._extract_delta(chunk)
            if delta:
                yield delta

    async def generate_title(
        self,
        messages: list[MessageRecord],
        model_id: str | None,
    ) -> str:
        provider, resolved_model = self._resolve_provider(model_id)
        logger.debug("chat.title.start provider=%s model_id=%s", provider, resolved_model)
        llm = self._build_llm(provider, resolved_model, streaming=False)
        if llm is None:
            raise RuntimeError("Requested model is not available.")
        prompt = (
            "Summarize the user's request as a short chat title. "
            "Return only the title text, max 20 characters."
        )
        user_text = generate_fallback_title(messages)
        title_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                ("human", "{user_text}"),
            ]
        )
        if provider == "gcp":
            llm = llm.bind(temperature=0.2)
        elif provider == "azure":
            llm = llm.bind(temperature=0.2)
        elif provider == "ollama":
            llm = llm.bind()
        else:
            llm = llm.bind(max_tokens=40, temperature=0.2)
        chain = title_prompt | llm
        response = await chain.ainvoke({"user_text": user_text})
        title = (response.content or "").strip()
        logger.debug(
            "chat.title.result provider=%s model_id=%s title=%s",
            provider,
            resolved_model,
            title,
        )
        return title
