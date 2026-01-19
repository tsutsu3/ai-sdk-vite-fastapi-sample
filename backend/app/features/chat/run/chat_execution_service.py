from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from langchain_core.messages import SystemMessage
from pydantic import BaseModel

from app.ai.chains.chat_chain import build_chat_chain
from app.ai.history.factory import build_history_factory
from app.ai.llms.factory import build_chat_model, resolve_chat_model
from app.ai.models import MemoryPolicy
from app.ai.ports import RetrieverBuilder
from app.ai.runtime import ChatRuntime
from app.core.config import AppConfig, ChatCapabilities
from app.features.chat.run.errors import RunServiceError
from app.features.chat.run.models import StreamContext
from app.features.chat.run.retrieval_context import build_retrieval_context
from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.features.retrieval.tools import ToolRegistry
from app.shared.llm_resolver import resolve_chat_model_spec

logger = getLogger(__name__)


class ToolExecutionPlan(BaseModel):
    """Computed inputs for tool-based chat execution."""

    system_prompt: str
    request_payload: list[dict[str, Any]]


class ChatExecutionService:
    """Execute chat/tool flows without streaming or persistence concerns.

    This service resolves model runtimes (with per-model caching), constructs
    retrieval-aware prompts, and streams token deltas from the selected runtime.
    It does not emit events or persist data; it only performs LLM execution and
    returns raw deltas plus request payloads for usage tracking.
    """

    def __init__(
        self,
        *,
        message_repo: MessageRepository,
        chat_runtime: ChatRuntime | None,
        app_config: AppConfig | None,
        chat_caps: ChatCapabilities | None,
        retriever_builder: RetrieverBuilder | None,
        tool_registry: ToolRegistry | None,
        runtime_cache: dict[str, ChatRuntime],
    ) -> None:
        self._message_repo = message_repo
        self._chat_runtime = chat_runtime
        self._app_config = app_config
        self._chat_caps = chat_caps
        self._retriever_builder = retriever_builder
        self._tool_registry = tool_registry
        self._runtime_cache = runtime_cache

    def has_base_runtime(self) -> bool:
        """Report whether the base runtime is configured."""
        return self._chat_runtime is not None

    def extract_user_text(self, messages: list[MessageRecord]) -> str:
        """Pull the most recent user text from message history."""
        for message in reversed(messages):
            if message.role != "user":
                continue
            text_parts = [part.text or "" for part in message.parts if part.type == "text"]
            content = " ".join(part.strip() for part in text_parts if part).strip()
            if content:
                return content
        return ""

    def build_chat_request_payload(self, user_text: str) -> list[dict[str, Any]]:
        """Build the minimal request payload for usage accounting."""
        return [{"role": "user", "content": user_text}]

    async def build_retrieval_context(self, context: StreamContext):
        """Resolve retrieval context or return None when tools are unused."""
        if context.tool_id and (not self._app_config or not self._tool_registry):
            raise RunServiceError("Retrieval service is not configured.")
        if not context.tool_id:
            return None
        return await build_retrieval_context(
            tool_id=context.tool_id,
            messages=context.messages,
            app_config=self._app_config,
            tenant_id=context.tenant_id,
            tool_registry=self._tool_registry,
            retriever_builder=self._retriever_builder,
        )

    def build_tool_request_payload(
        self,
        context: StreamContext,
        retrieval_context,
    ) -> list[dict[str, Any]]:
        """Build the full request payload including tool context."""
        langchain_payload = list(context.langchain_messages)
        if retrieval_context:
            # Inject retrieval system prompt ahead of the chat history.
            langchain_payload = [
                SystemMessage(content=retrieval_context.system_message),
                *langchain_payload,
            ]
        return [
            {"role": message.type, "content": message.content} for message in langchain_payload
        ]

    def build_tool_execution_plan(
        self,
        context: StreamContext,
        retrieval_context,
    ) -> ToolExecutionPlan:
        """Package tool execution inputs for the coordinator."""
        system_prompt = retrieval_context.system_message if retrieval_context else ""
        request_payload = self.build_tool_request_payload(context, retrieval_context)
        return ToolExecutionPlan(
            system_prompt=system_prompt,
            request_payload=request_payload,
        )

    def _resolve_chat_runtime(self, model_id: str | None) -> ChatRuntime | None:
        """Resolve and cache a runtime for the requested model."""
        if not model_id or not self._app_config or not self._chat_caps:
            return self._chat_runtime

        # Reuse cached runtimes per model id.
        cached = self._runtime_cache.get(model_id)
        if cached:
            return cached

        try:
            model_spec = resolve_chat_model_spec(
                self._app_config,
                self._chat_caps,
                resolve_chat_model,
                model_id,
            )
        except RuntimeError:
            logger.warning("run.stream.model_unavailable model_id=%s", model_id)
            return self._chat_runtime

        llm = build_chat_model(self._app_config, model_spec, streaming=True)
        history_factory = build_history_factory(
            self._message_repo,
            MemoryPolicy(),
            write_enabled=False,
        )
        chat_chain = build_chat_chain(llm, history_factory=history_factory)
        runtime = ChatRuntime(chat_chain, llm, history_factory)
        self._runtime_cache[model_id] = runtime
        return runtime

    async def stream_chat(
        self,
        *,
        context: StreamContext,
        user_text: str,
    ) -> AsyncIterator[str]:
        """Stream a standard chat response."""
        runtime = self._resolve_chat_runtime(context.model_id)
        if runtime is None:
            raise RunServiceError("Chat runtime is not configured.")

        session_id = f"{context.tenant_id}::{context.user_id}::{context.conversation_id}"
        async for delta in runtime.stream_text(
            input_text=user_text,
            session_id=session_id,
        ):
            yield delta

    async def stream_tool(
        self,
        *,
        context: StreamContext,
        user_text: str,
        system_prompt: str,
    ) -> AsyncIterator[str]:
        """Stream a tool-augmented response with a system prompt."""
        runtime = self._resolve_chat_runtime(context.model_id)
        if runtime is None:
            raise RunServiceError("Chat runtime is not configured.")

        async for delta in runtime.stream_text_with_system(
            input_text=user_text,
            session_id=f"{context.tenant_id}::{context.user_id}::{context.conversation_id}",
            system_prompt=system_prompt or "You are a helpful assistant.",
        ):
            yield delta
