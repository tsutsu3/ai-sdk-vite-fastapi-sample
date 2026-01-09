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
from langchain_core.messages import BaseMessage, SystemMessage

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
from app.features.retrieval.service import RetrievalService
from app.features.run.errors import RunServiceError
from app.features.run.message_utils import (
    extract_conversation_id,
    extract_file_ids,
    extract_messages,
    extract_model_id,
    select_latest_user_message,
    to_langchain_messages,
)
from app.features.run.models import RunRequest, StreamContext
from app.features.run.retrieval_context import build_retrieval_context
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
        retrieval_service: RetrievalService | None = None,
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
        self._retrieval_service = retrieval_service
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
        message_id, model_id, langchain_messages = self._build_message_context(
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
            langchain_messages=langchain_messages,
            web_search=extract_web_search(payload),
            tool_id=payload.tool_id,
        )

        logger.info(
            "run.stream.start conversation_id=%s model_id=%s tool_id=%s web_search=%s",
            conversation_id,
            model_id,
            payload.tool_id,
            context.web_search.enabled,
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
            tool_id="chat",
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
    ) -> tuple[str, str | None, list[BaseMessage]]:
        """Build message context for streaming.

        This resolves the message id, model id, and LangChain messages.

        Args:
            payload: Chat request payload.
            messages: Parsed chat messages.

        Returns:
            tuple[str, str | None, list[BaseMessage]]: Message id, model id,
            and formatted messages.
        """
        message_id = f"msg-{uuid.uuid4()}"
        model_id = extract_model_id(payload)
        langchain_messages = to_langchain_messages(messages)
        return message_id, model_id, langchain_messages

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
            tool_id="chat",
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
            langchain_payload = list(context.langchain_messages)
            if context.tool_id and not self._retrieval_service:
                raise RunServiceError("Retrieval service is not configured.")
            if context.tool_id and self._retrieval_service:
                reasoning_id = f"reasoning_{uuid.uuid4()}"
                yield ReasoningStartEvent(id=reasoning_id)
                yield ReasoningDeltaEvent(
                    id=reasoning_id,
                    delta=f"Retrieval tool: {context.tool_id}\n",
                )
                retrieval_context = await build_retrieval_context(
                    tool_id=context.tool_id,
                    messages=context.messages,
                    retrieval_service=self._retrieval_service,
                )
                if retrieval_context:
                    logger.debug(
                        "run.retrieval.context tool_id=%s results=%s",
                        context.tool_id,
                        len(retrieval_context.results),
                    )
                    langchain_payload = [
                        SystemMessage(content=retrieval_context.system_message),
                        *langchain_payload,
                    ]
                    query_preview = retrieval_context.query
                    if len(query_preview) > 120:
                        query_preview = query_preview[:117].rstrip() + "..."
                    yield ReasoningDeltaEvent(
                        id=reasoning_id,
                        delta=f"Query: {query_preview}\n",
                    )
                    yield ReasoningDeltaEvent(
                        id=reasoning_id,
                        delta=f"Retrieved {len(retrieval_context.results)} results.\n",
                    )
                else:
                    yield ReasoningDeltaEvent(
                        id=reasoning_id,
                        delta="No retrieval context was added.\n",
                    )
                yield ReasoningEndEvent(id=reasoning_id)
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
                        logger.info("run.web_search.failed engine=%s", provider.id)
                    else:
                        if results:
                            logger.debug(
                                "run.web_search.results engine=%s count=%s",
                                provider.id,
                                len(results),
                            )
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
                            langchain_payload = [
                                SystemMessage(content=search_block),
                                *langchain_payload,
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
            request_payload = [
                {"role": message.type, "content": message.content}
                for message in langchain_payload
            ]
            async for delta in self._streamer.stream_chat(langchain_payload, context.model_id):
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
            tool_id="chat",
        )
        logger.debug(
            "run.stream.response_raw conversation_id=%s message_id=%s model_id=%s text=%s",
            context.conversation_id,
            context.message_id,
            context.model_id,
            response_text,
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
        logger.info(
            "run.stream.done conversation_id=%s message_id=%s bytes_out=%s",
            context.conversation_id,
            context.message_id,
            len(response_text.encode("utf-8")) if response_text else 0,
        )
