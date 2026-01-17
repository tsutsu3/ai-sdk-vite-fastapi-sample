import asyncio
import uuid
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from fastapi_ai_sdk.models import (
    AnyStreamEvent,
    DataEvent,
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    ReasoningStartEvent,
)
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field

from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_user_id,
)
from app.features.chat.run.chat_execution_service import ChatExecutionService
from app.features.chat.run.errors import RunServiceError
from app.features.chat.run.message_utils import (
    extract_messages,
    extract_model_id,
    select_latest_user_message,
    to_langchain_messages,
)
from app.features.chat.run.models import RunRequest, StreamContext
from app.features.chat.run.persistence_service import PersistenceService
from app.features.chat.run.streamers import ChatStreamer
from app.features.messages.models import MessageRecord
from app.features.title.title_generator import TitleGenerator

logger = getLogger(__name__)


class ResponseBuffer(BaseModel):
    """Accumulates streamed response text."""

    text: str = ""


class TitleState(BaseModel):
    """Tracks title generation lifecycle state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    final_title: str
    sent: bool = False
    task: asyncio.Task[str] | None = None


class UsagePayloadState(BaseModel):
    """Holds request payloads for usage reporting."""

    payload: list[dict[str, Any]] = Field(default_factory=list)


class StreamCoordinator:
    """Coordinate streaming order, branching, and title lifecycle.

    This orchestrates the end-to-end stream: it prepares message context,
    dispatches chat vs. tool execution, and guarantees event ordering
    (start/conversation/model/delta/end/error). It also owns title generation
    task management so updates are emitted and persisted once, and delegates
    all execution and persistence to the injected services.
    """

    def __init__(
        self,
        *,
        streamer: ChatStreamer,
        title_generator: TitleGenerator,
        execution: ChatExecutionService,
        persistence: PersistenceService,
    ) -> None:
        self._streamer = streamer
        self._title_generator = title_generator
        self._execution = execution
        self._persistence = persistence

    async def stream(self, payload: RunRequest) -> AsyncIterator[AnyStreamEvent]:
        """Prepare context and return the streaming iterator."""
        tenant_id = get_current_tenant_id()
        user_id = get_current_user_id()
        conversation_id, messages, title, should_generate_title = (
            await self._persistence.prepare_conversation(
                payload,
                tenant_id,
                user_id,
            )
        )
        incoming_messages = select_latest_user_message(extract_messages(payload))
        merged_messages = self._merge_messages(messages, incoming_messages)
        message_id, model_id, langchain_messages = self._build_message_context(
            payload,
            merged_messages,
        )
        logger.debug("Chat messages: %s", _format_messages_for_log(merged_messages))

        context = StreamContext(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            title=title,
            should_generate_title=should_generate_title,
            messages=merged_messages,
            langchain_messages=langchain_messages,
            tool_id=payload.tool_id,
        )

        logger.info(
            "run.stream.start conversation_id=%s model_id=%s tool_id=%s",
            conversation_id,
            model_id,
            payload.tool_id,
        )

        return self._stream_with_persistence(context=context)

    def _merge_messages(
        self,
        existing: list[MessageRecord],
        incoming: list[MessageRecord],
    ) -> list[MessageRecord]:
        """Merge incoming messages into the existing history by id."""
        if not incoming:
            return list(existing)
        merged = list(existing)
        index_by_id = {message.id: idx for idx, message in enumerate(merged)}
        for message in incoming:
            if message.id in index_by_id:
                merged[index_by_id[message.id]] = message
            else:
                index_by_id[message.id] = len(merged)
                merged.append(message)
        return merged

    def _build_message_context(
        self,
        payload: RunRequest,
        messages: list[MessageRecord],
    ) -> tuple[str, str | None, list[BaseMessage]]:
        """Build identifiers and LangChain payload from messages."""
        message_id = f"msg-{uuid.uuid4()}"
        model_id = extract_model_id(payload)
        langchain_messages = to_langchain_messages(messages)
        return message_id, model_id, langchain_messages

    def _send_conversation_event(self, context: StreamContext) -> AnyStreamEvent:
        """Emit the conversation id event."""
        return DataEvent.create(
            "conversation",
            {"convId": context.conversation_id},
        )

    def _send_model_event(self, context: StreamContext) -> AnyStreamEvent | None:
        """Emit the selected model id event if present."""
        if not context.model_id:
            return None
        return DataEvent.create(
            "model",
            {"messageId": context.message_id, "modelId": context.model_id},
        )

    async def _maybe_emit_title_update(
        self,
        *,
        context: StreamContext,
        title_state: TitleState,
        force: bool,
    ) -> AnyStreamEvent | None:
        """Optionally emit and persist title updates."""
        task = title_state.task

        if not task or title_state.sent:
            return None

        if force and not task.done():
            try:
                await task
            except Exception:
                return None

        if not task.done():
            return None

        try:
            generated = task.result()
        except Exception:
            return None

        if not generated:
            return None

        title_state.sent = True
        title_state.final_title = generated

        await self._persistence.save_title(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            title=generated,
        )

        return DataEvent.create("title", {"title": generated})

    async def _stream_with_persistence(
        self,
        *,
        context: StreamContext,
    ) -> AsyncIterator[AnyStreamEvent]:
        """Stream events while coordinating execution and persistence."""
        async for event in self._yield_start_events(context):
            yield event

        response_buffer, usage_state, title_state = self._init_states(context)

        failed = False
        try:
            self._ensure_runtime()
            if not context.tool_id:
                async for event in self._stream_chat_branch(
                    context=context,
                    response_buffer=response_buffer,
                    usage_state=usage_state,
                ):
                    yield event
            else:
                async for event in self._stream_tool_branch(
                    context=context,
                    response_buffer=response_buffer,
                    usage_state=usage_state,
                    title_state=title_state,
                ):
                    yield event
        except Exception as exc:
            failed = True
            async for event in self._stream_error(exc, context):
                yield event
        finally:
            # Title emission is centralized to avoid duplicate code paths.
            title_event = await self._maybe_emit_title_update(
                context=context,
                title_state=title_state,
                force=True,
            )
            if title_event:
                yield title_event

        if failed:
            return

        async for event in self._finalize_success(
            context=context,
            response_buffer=response_buffer,
            usage_state=usage_state,
            title_state=title_state,
        ):
            yield event

    async def _yield_start_events(
        self,
        context: StreamContext,
    ) -> AsyncIterator[AnyStreamEvent]:
        start_event = self._streamer.ensure_message_start(context.message_id)
        if start_event:
            yield start_event

        yield self._send_conversation_event(context)

        model_event = self._send_model_event(context)
        if model_event:
            yield model_event

    def _init_states(
        self,
        context: StreamContext,
    ) -> tuple[ResponseBuffer, UsagePayloadState, TitleState]:
        response_buffer = ResponseBuffer()
        usage_state = UsagePayloadState()
        title_state = TitleState(final_title=context.title)
        if context.should_generate_title:
            # Title generation runs in parallel with streaming.
            title_state.task = asyncio.create_task(
                self._title_generator.generate(context.messages)
            )
        return response_buffer, usage_state, title_state

    def _ensure_runtime(self) -> None:
        if not self._execution.has_base_runtime():
            raise RunServiceError("LCEL runtime is not configured.")

    async def _stream_error(
        self,
        exc: Exception,
        context: StreamContext,
    ) -> AsyncIterator[AnyStreamEvent]:
        logger.exception(
            "run.stream.error conversation_id=%s message_id=%s model_id=%s tool_id=%s",
            context.conversation_id,
            context.message_id,
            context.model_id,
            context.tool_id,
        )
        error_text = f"{exc}"
        async for chunk in self._streamer.error_stream(error_text):
            yield chunk

    async def _stream_chat_branch(
        self,
        *,
        context: StreamContext,
        response_buffer: ResponseBuffer,
        usage_state: UsagePayloadState,
    ) -> AsyncIterator[AnyStreamEvent]:
        user_text = self._execution.extract_user_text(context.messages)
        if not user_text:
            raise RunServiceError("Missing user input.")

        usage_state.payload = self._execution.build_chat_request_payload(user_text)
        async for delta in self._execution.stream_chat(
            context=context,
            user_text=user_text,
        ):
            response_buffer.text += delta
            async for chunk in self._streamer.stream_text_delta(delta, context.message_id):
                yield chunk

    async def _stream_tool_branch(
        self,
        *,
        context: StreamContext,
        response_buffer: ResponseBuffer,
        usage_state: UsagePayloadState,
        title_state: TitleState,
    ) -> AsyncIterator[AnyStreamEvent]:
        retrieval_context = await self._execution.build_retrieval_context(context)
        reasoning_id = f"reasoning_{uuid.uuid4()}"
        yield ReasoningStartEvent(id=reasoning_id)
        yield ReasoningDeltaEvent(
            id=reasoning_id,
            delta=f"Retrieval tool: {context.tool_id}\n",
        )
        if retrieval_context:
            logger.debug(
                "run.retrieval.context tool_id=%s results=%s",
                context.tool_id,
                len(retrieval_context.results),
            )
            query_preview = retrieval_context.query
            if len(query_preview) > 120:
                query_preview = query_preview[:117].rstrip() + "..."
            yield ReasoningDeltaEvent(
                id=reasoning_id,
                delta=f"Query: {query_preview}\n",
            )
            yield ReasoningDeltaEvent(
                id=reasoning_id,
                delta=(f"Retrieved {len(retrieval_context.results)} results.\n"),
            )
        else:
            yield ReasoningDeltaEvent(
                id=reasoning_id,
                delta="No retrieval context was added.\n",
            )
        yield ReasoningEndEvent(id=reasoning_id)

        user_text = self._execution.extract_user_text(context.messages)
        if not user_text:
            raise RunServiceError("Missing user input.")

        plan = self._execution.build_tool_execution_plan(
            context,
            retrieval_context,
        )
        usage_state.payload = plan.request_payload
        async for delta in self._execution.stream_tool(
            context=context,
            user_text=user_text,
            system_prompt=plan.system_prompt,
        ):
            response_buffer.text += delta
            async for chunk in self._streamer.stream_text_delta(delta, context.message_id):
                yield chunk

            title_event = await self._maybe_emit_title_update(
                context=context,
                title_state=title_state,
                force=False,
            )
            if title_event:
                yield title_event

    async def _finalize_success(
        self,
        *,
        context: StreamContext,
        response_buffer: ResponseBuffer,
        usage_state: UsagePayloadState,
        title_state: TitleState,
    ) -> AsyncIterator[AnyStreamEvent]:
        await self._persistence.save_messages(context, response_buffer.text)
        async for chunk in self._streamer.stream_text_end(context.message_id):
            yield chunk

        await self._persistence.save_conversation_final(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            final_title=title_state.final_title,
        )
        logger.debug(
            "run.stream.response_raw conversation_id=%s message_id=%s model_id=%s",
            context.conversation_id,
            context.message_id,
            context.model_id,
        )
        await self._persistence.record_usage(
            context,
            usage_state.payload,
            response_buffer.text,
        )
        logger.info(
            "run.stream.done conversation_id=%s message_id=%s bytes_out=%s",
            context.conversation_id,
            context.message_id,
            len(response_buffer.text.encode("utf-8")) if response_buffer.text else 0,
        )


def _truncate_text(text: str, limit: int = 80) -> str:
    """Truncate logged text to keep logs readable."""
    return text if len(text) <= limit else text[:limit] + "..."


def _format_messages_for_log(messages, text_limit: int = 80):
    formatted = []

    for m in messages:
        md = m.model_dump()

        parts = []
        for p in md.get("parts", []):
            if p.get("type") == "text" and isinstance(p.get("text"), str):
                p = {
                    **p,
                    "text": _truncate_text(p["text"], text_limit),
                }
            parts.append(p)

        formatted.append(
            {
                **{k: v for k, v in md.items() if k != "parts"},
                "parts": parts,
            }
        )

    return formatted
