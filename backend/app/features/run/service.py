import asyncio
import json
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

from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_user_id,
)
from app.features.conversations.ports import ConversationRepository
from app.features.messages.models import (
    MessagePartRecord,
    MessageRecord,
)
from app.features.messages.ports import MessageRepository
from app.features.run.message_utils import (
    extract_conversation_id,
    extract_file_ids,
    extract_messages,
    extract_model_id,
    select_latest_user_message,
    to_openai_messages,
)
from app.features.run.models import OpenAIMessage, RunRequest, StreamContext
from app.features.run.streamers import ChatStreamer
from app.features.run.web_search_utils import (
    WebSearchContentFetcher,
    extract_search_query,
    extract_web_search,
    format_web_search_results,
)
from app.features.title.title_generator import TitleGenerator
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.features.web_search.service import WebSearchService
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime

logger = getLogger(__name__)


class RunService:
    """Service that orchestrates chat execution and streaming.

    This service coordinates message persistence, model selection, web search,
    and streaming event assembly so providers and repositories remain decoupled.
    It is the main integration point between request payloads and AI SDK output.
    """

    def __init__(
        self,
        streamer: ChatStreamer,
        title_generator: TitleGenerator,
        web_search: WebSearchService,
        fetch_web_search_content: bool = False,
    ) -> None:
        """Initialize the run service.

        Args:
            streamer: Chat streamer implementation.
            title_generator: Title generator.
            web_search: Web search service.
            fetch_web_search_content: Whether to fetch page content.
        """
        self._streamer = streamer
        self._title_generator = title_generator
        self._web_search = web_search
        self._fetch_web_search_content = fetch_web_search_content
        self._web_search_content_fetcher = WebSearchContentFetcher()

    async def stream(
        self,
        payload: RunRequest,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> AsyncIterator[AnyStreamEvent]:
        """Stream chat events for the given payload.

        This is the primary entry point used by the chat API to produce
        incremental AI SDK events while persisting conversation state.

        Args:
            payload: Chat request payload.
            conversation_repo: Conversation repository.
            message_repo: Message repository.
            usage_repo: Usage repository.

        Returns:
            AsyncIterator[AnyStreamEvent]: Stream of AI SDK events.
        """
        tenant_id = get_current_tenant_id()
        user_id = get_current_user_id()
        conversation_id, messages, title, should_generate_title = (
            await self._prepare_conversation(
                payload,
                conversation_repo,
                message_repo,
                tenant_id,
                user_id,
            )
        )
        incoming_messages = select_latest_user_message(extract_messages(payload))
        merged_messages = self._merge_messages(messages, incoming_messages)
        await self._persist_incoming_messages(
            payload,
            message_repo,
            tenant_id,
            user_id,
            conversation_id,
            incoming_messages,
        )
        message_id, model_id, openai_messages = self._build_message_context(
            payload,
            merged_messages,
        )

        context = StreamContext(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            title=title,
            should_generate_title=should_generate_title,
            messages=merged_messages,
            openai_messages=openai_messages,
            web_search=extract_web_search(payload),
        )

        return self._stream_with_persistence(
            context=context,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            usage_repo=usage_repo,
        )

    def _merge_messages(
        self,
        existing: list[MessageRecord],
        incoming: list[MessageRecord],
    ) -> list[MessageRecord]:
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

    async def _prepare_conversation(
        self,
        payload: RunRequest,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        tenant_id: str,
        user_id: str,
    ) -> tuple[str, list[MessageRecord], str, bool]:
        """Prepare conversation state for a chat request.

        This ensures a conversation exists and determines whether a title
        should be generated during the run.

        Args:
            payload: Chat request payload.
            conversation_repo: Conversation repository.
            tenant_id: Tenant identifier.
            user_id: User identifier.

        Returns:
            tuple[str, list[MessageRecord], str, bool]: Conversation id, messages,
            existing title, and title-generation flag.
        """
        conversation_id = extract_conversation_id(payload)
        messages, _ = await message_repo.list_messages(
            tenant_id,
            user_id,
            conversation_id,
            limit=None,
            continuation_token=None,
            descending=False,
        )
        existing = await conversation_repo.get_conversation(tenant_id, user_id, conversation_id)
        title = existing.title if existing else DEFAULT_CHAT_TITLE
        should_generate_title = not title or title == DEFAULT_CHAT_TITLE
        await conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            title,
        )
        return conversation_id, messages, title, should_generate_title

    async def _persist_incoming_messages(
        self,
        payload: RunRequest,
        message_repo: MessageRepository,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> None:
        """Persist incoming user messages before streaming a response.

        This ensures the user input is saved even if streaming fails.

        Args:
            payload: Chat request payload.
            message_repo: Message repository.
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            messages: Parsed incoming messages.
        """
        if not messages:
            return
        file_ids = extract_file_ids(payload)
        if file_ids and messages:
            last_message = messages[-1]
            existing_ids = {
                part.file_id
                for part in last_message.parts
                if part.type == "file" and part.file_id
            }
            next_parts = list(last_message.parts)
            for file_id in file_ids:
                if file_id in existing_ids:
                    continue
                next_parts.append(MessagePartRecord(type="file", file_id=file_id))
            updated_message = last_message.model_copy(update={"parts": next_parts})
            messages = [*messages[:-1], updated_message]
        await message_repo.upsert_messages(tenant_id, user_id, conversation_id, messages)

    def _build_message_context(
        self,
        payload: RunRequest,
        messages: list[MessageRecord],
    ) -> tuple[str, str | None, list[OpenAIMessage]]:
        """Build message context for streaming.

        This resolves the message id, model id, and OpenAI-formatted messages.

        Args:
            payload: Chat request payload.
            messages: Parsed chat messages.

        Returns:
            tuple[str, str | None, list[OpenAIMessage]]: Message id, model id,
            and formatted messages.
        """
        message_id = f"msg-{uuid.uuid4()}"
        model_id = extract_model_id(payload)
        openai_messages = to_openai_messages(messages)
        return message_id, model_id, openai_messages

    async def _send_title_update(
        self,
        conversation_repo: ConversationRepository,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        generated: str,
    ) -> AnyStreamEvent:
        """Persist and emit a title update event.

        This keeps the conversation metadata in sync with streamed title events.

        Args:
            conversation_repo: Conversation repository.
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            generated: Generated title.

        Returns:
            AnyStreamEvent: Data event with the updated title.
        """
        await conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            generated,
        )
        return DataEvent.create("title", {"title": generated})

    def _send_conversation_event(self, context: StreamContext) -> AnyStreamEvent:
        return DataEvent.create(
            "conversation",
            {"convId": context.conversation_id},
        )

    def _send_model_event(self, context: StreamContext) -> AnyStreamEvent | None:
        if not context.model_id:
            return None
        return DataEvent.create(
            "model",
            {"messageId": context.message_id, "modelId": context.model_id},
        )

    async def _stream_with_persistence(
        self,
        *,
        context: StreamContext,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> AsyncIterator[AnyStreamEvent]:
        """Stream events while persisting messages and metadata.

        This method coordinates streaming with title updates, message
        persistence, and usage recording to keep state consistent.

        Args:
            context: Stream context data.
            conversation_repo: Conversation repository.
            message_repo: Message repository.
            usage_repo: Usage repository.

        Returns:
            AsyncIterator[AnyStreamEvent]: Stream of AI SDK events.
        """
        start_event = self._streamer.ensure_message_start(context.message_id)
        if start_event:
            yield start_event
        yield self._send_conversation_event(context)
        model_event = self._send_model_event(context)
        if model_event:
            yield model_event
        response_text = ""
        final_title = context.title
        title_task: asyncio.Task[str] | None = None
        if context.should_generate_title:
            title_task = asyncio.create_task(self._title_generator.generate(context.messages))
        title_sent = False
        request_payload: list[dict[str, Any]] = []
        try:
            openai_payload = list(context.openai_messages)
            request_payload = [
                message.model_dump(by_alias=True, exclude_none=True) for message in openai_payload
            ]
            if context.web_search.enabled:
                start_event = self._streamer.ensure_message_start(context.message_id)
                if start_event:
                    yield start_event
                query = extract_search_query(context.messages)
                provider = self._web_search.resolve_engine(context.web_search.engine)
                logger.debug(
                    "Web search enabled. requested_engine=%s resolved_engine=%s",
                    context.web_search.engine,
                    provider.id if provider else None,
                )
                if query and provider:
                    reasoning_id = f"reasoning_{uuid.uuid4()}"
                    yield ReasoningStartEvent(id=reasoning_id)
                    yield ReasoningDeltaEvent(
                        id=reasoning_id,
                        delta=f"Searching the web for: {query}\n",
                    )
                    try:
                        results = list(
                            await self._web_search.search(
                                query,
                                engine=provider.id,
                            )
                        )
                    except Exception:
                        results = []
                        yield ReasoningDeltaEvent(
                            id=reasoning_id,
                            delta="Search failed.\n",
                        )
                    else:
                        if results:
                            content_by_url = None
                            if self._fetch_web_search_content:
                                content_by_url = await self._web_search_content_fetcher.fetch(
                                    results
                                )
                            search_block = format_web_search_results(
                                provider.name,
                                results,
                                content_by_url=content_by_url,
                            )
                            # logger.debug("Web search results: %s", search_block)
                            openai_payload = [
                                OpenAIMessage(role="system", content=search_block),
                                *openai_payload,
                            ]
                            request_payload = [
                                message.model_dump(by_alias=True, exclude_none=True)
                                for message in openai_payload
                            ]
                            yield ReasoningDeltaEvent(
                                id=reasoning_id,
                                delta=f"Found {len(results)} results.\n",
                            )
                            for index, result in enumerate(results, start=1):
                                yield ReasoningDeltaEvent(
                                    id=reasoning_id,
                                    delta=f"{index}. {result.title}\n{result.url}\n",
                                )
                            if self._fetch_web_search_content:
                                yield ReasoningDeltaEvent(
                                    id=reasoning_id,
                                    delta="\nFetching content from result URLs...\n",
                                )
                        else:
                            yield ReasoningDeltaEvent(
                                id=reasoning_id,
                                delta="No results found.\n",
                            )
                    yield ReasoningEndEvent(id=reasoning_id)
            async for delta in self._streamer.stream_chat(openai_payload, context.model_id):
                response_text += delta
                async for chunk in self._streamer.stream_text_delta(delta, context.message_id):
                    yield chunk
                if title_task and not title_sent and title_task.done():
                    generated = title_task.result()
                    title_sent = True
                    final_title = generated
                    yield await self._send_title_update(
                        conversation_repo,
                        context.tenant_id,
                        context.user_id,
                        context.conversation_id,
                        generated,
                    )
        except Exception as exc:
            error_text = f"{exc}"
            async for chunk in self._streamer.error_stream(error_text):
                yield chunk
            return
        finally:
            if title_task and not title_task.done():
                try:
                    await title_task
                except Exception:
                    pass
            if title_task and not title_sent:
                try:
                    generated = title_task.result()
                except Exception:
                    generated = ""
                if generated:
                    title_sent = True
                    final_title = generated
                    yield await self._send_title_update(
                        conversation_repo,
                        context.tenant_id,
                        context.user_id,
                        context.conversation_id,
                        generated,
                    )

        async for chunk in self._streamer.stream_text_end(context.message_id):
            yield chunk
        parent_message_id = context.messages[-1].id if context.messages else ""
        assistant_message = MessageRecord(
            id=context.message_id,
            role="assistant",
            parts=[MessagePartRecord(type="text", text=response_text)],
            created_at=now_datetime(),
            parent_message_id=parent_message_id,
            model_id=context.model_id,
        )
        await message_repo.upsert_messages(
            context.tenant_id,
            context.user_id,
            context.conversation_id,
            [assistant_message],
        )
        await conversation_repo.upsert_conversation(
            context.tenant_id,
            context.user_id,
            context.conversation_id,
            final_title,
        )
        await usage_repo.record_usage(
            UsageRecord(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                message_id=context.message_id,
                model_id=context.model_id,
                tokens_in=None,
                tokens_out=None,
                bytes_in=(
                    len(json.dumps(request_payload).encode("utf-8")) if request_payload else None
                ),
                bytes_out=len(response_text.encode("utf-8")) if response_text else None,
                requests=1,
            )
        )
