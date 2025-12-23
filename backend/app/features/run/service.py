import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from logging import getLogger
import re
from html import unescape

from pydantic import ValidationError
import httpx

from fastapi_ai_sdk.models import (
    AnyStreamEvent,
    DataEvent,
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    ReasoningStartEvent,
)
from app.features.chat.streamers import ChatStreamer
from app.features.conversations.ports import ConversationRepository
from app.features.messages.models import ChatMessage, MessageMetadata, MessagePart
from app.features.messages.ports import MessageRepository
from app.features.run.models import OpenAIMessage, StreamContext, WebSearchRequest
from app.features.web_search.models import WebSearchResult
from app.features.web_search.service import WebSearchService
from app.features.title.title_generator import TitleGenerator
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.request_context import get_current_tenant_id, get_current_user_id

logger = getLogger(__name__)


def extract_messages(payload: dict[str, Any]) -> list[ChatMessage]:
    messages = payload.get("messages")
    if isinstance(messages, list):
        parsed: list[ChatMessage] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            try:
                parsed.append(ChatMessage.model_validate(message))
            except ValidationError:
                continue
        return parsed
    return []


def extract_conversation_id(payload: dict[str, Any]) -> str:
    for key in ("conversationId", "chatId", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return f"conv-{uuid.uuid4().hex}"


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_model_id(payload: dict[str, Any]) -> str | None:
    model = payload.get("model")
    return model if isinstance(model, str) and model else None


def extract_file_ids(payload: dict[str, Any]) -> list[str]:
    file_ids = payload.get("fileIds")
    if isinstance(file_ids, list):
        return [str(file_id) for file_id in file_ids]
    return []


def extract_web_search(payload: dict[str, Any]) -> WebSearchRequest:
    enabled = False
    engine: str | None = None
    raw = payload.get("webSearch")
    if raw is None:
        raw = payload.get("websearch")
    if isinstance(raw, bool):
        enabled = raw
    elif isinstance(raw, str):
        enabled = True
        engine = raw.strip()
    elif isinstance(raw, dict):
        enabled = bool(raw.get("enabled") or raw.get("use") or raw.get("value"))
        engine_value = raw.get("engine") or raw.get("id")
        if isinstance(engine_value, str):
            engine = engine_value.strip()

    if not engine:
        engine_value = payload.get("webSearchEngine") or payload.get("websearchEngine")
        if isinstance(engine_value, str):
            engine = engine_value.strip()

    return WebSearchRequest(enabled=enabled, engine=engine or None)


def extract_search_query(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role != "user":
            continue
        text_parts = [part.text or "" for part in message.parts if part.type == "text"]
        query = " ".join(part.strip() for part in text_parts if part).strip()
        if query:
            return query
    return ""


def _strip_html_content(raw: str) -> str:
    text = raw[:200000]
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\\s+", " ", text).strip()


def format_web_search_results(
    engine: str,
    results: list[WebSearchResult],
    content_by_url: dict[str, str] | None = None,
) -> str:
    lines = [f"Web search results from {engine}:"]
    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result.title}")
        lines.append(f"   URL: {result.url}")
        if result.snippet:
            lines.append(f"   Snippet: {result.snippet}")
        if content_by_url:
            content = content_by_url.get(result.url, "")
            if content:
                lines.append(f"   Content: {content}")
    return "\n".join(lines)


def to_openai_messages(messages: list[ChatMessage]) -> list[OpenAIMessage]:
    converted: list[OpenAIMessage] = []
    for message in messages:
        text_parts = [part.text or "" for part in message.parts if part.type == "text"]
        content = " ".join(part.strip() for part in text_parts if part).strip()
        if content:
            converted.append(OpenAIMessage(role=message.role, content=content))
    return converted


class RunService:
    def __init__(
        self,
        streamer: ChatStreamer,
        title_generator: TitleGenerator,
        web_search: WebSearchService,
        fetch_web_search_content: bool = False,
    ) -> None:
        self._streamer = streamer
        self._title_generator = title_generator
        self._web_search = web_search
        self._fetch_web_search_content = fetch_web_search_content
        self._web_search_content_limit = 2000

    async def _fetch_result_contents(
        self,
        results: list[WebSearchResult],
    ) -> dict[str, str]:
        if not results:
            return {}

        semaphore = asyncio.Semaphore(3)

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:

            async def fetch_one(result: WebSearchResult) -> tuple[str, str]:
                url = result.url
                async with semaphore:
                    try:
                        response = await client.get(
                            url,
                            headers={"User-Agent": "Mozilla/5.0"},
                        )
                        response.raise_for_status()
                    except httpx.HTTPError:
                        return (url, "")

                    content_type = response.headers.get("content-type", "")
                    if "text" not in content_type and "html" not in content_type:
                        return (url, "")

                    cleaned = _strip_html_content(response.text)
                    if not cleaned:
                        return (url, "")

                    return (url, cleaned[: self._web_search_content_limit])

            tasks = [fetch_one(result) for result in results]
            pairs = await asyncio.gather(*tasks, return_exceptions=False)
            return {url: content for url, content in pairs if content}

    async def _prepare_conversation(
        self,
        payload: dict[str, Any],
        conversation_repo: ConversationRepository,
        tenant_id: str,
        user_id: str,
    ) -> tuple[str, list[ChatMessage], str, bool]:
        conversation_id = extract_conversation_id(payload)
        messages = extract_messages(payload)
        existing = await conversation_repo.get_conversation(tenant_id, user_id, conversation_id)
        title = existing.title if existing else DEFAULT_CHAT_TITLE
        should_generate_title = not title or title == DEFAULT_CHAT_TITLE
        await conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            title,
            current_timestamp(),
        )
        return conversation_id, messages, title, should_generate_title

    async def _persist_incoming_messages(
        self,
        payload: dict[str, Any],
        message_repo: MessageRepository,
        tenant_id: str,
        conversation_id: str,
        messages: list[ChatMessage],
    ) -> None:
        file_ids = extract_file_ids(payload)
        if file_ids and messages:
            last_message = messages[-1]
            metadata = last_message.metadata or MessageMetadata()
            updated_metadata = metadata.model_copy(update={"file_ids": file_ids})
            updated_message = last_message.model_copy(update={"metadata": updated_metadata})
            messages = [*messages[:-1], updated_message]
        await message_repo.upsert_messages(tenant_id, conversation_id, messages)

    def _build_message_context(
        self,
        payload: dict[str, Any],
        messages: list[ChatMessage],
    ) -> tuple[str, str | None, list[OpenAIMessage]]:
        message_id = f"msg-{uuid.uuid4().hex}"
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
        await conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            generated,
            current_timestamp(),
        )
        return DataEvent.create("title", {"title": generated})

    async def _stream_with_persistence(
        self,
        *,
        context: StreamContext,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> AsyncIterator[AnyStreamEvent]:
        response_text = ""
        final_title = context.title
        title_task: asyncio.Task[str] | None = None
        if context.should_generate_title:
            title_task = asyncio.create_task(self._title_generator.generate(context.messages))
        title_sent = False
        try:
            openai_payload = [
                message.model_dump(by_alias=True, exclude_none=True)
                for message in context.openai_messages
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
                    reasoning_id = f"reasoning_{uuid.uuid4().hex}"
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
                            content_by_url = (
                                await self._fetch_result_contents(results)
                                if self._fetch_web_search_content
                                else None
                            )
                            search_block = format_web_search_results(
                                provider.name,
                                results,
                                content_by_url=content_by_url,
                            )
                            # logger.debug("Web search results: %s", search_block)
                            openai_payload = [
                                {"role": "system", "content": search_block},
                                *openai_payload,
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
        assistant_message = ChatMessage(
            id=context.message_id,
            role="assistant",
            parts=[MessagePart(type="text", text=response_text)],
        )
        await message_repo.upsert_messages(
            context.tenant_id,
            context.conversation_id,
            context.messages + [assistant_message],
        )
        await conversation_repo.upsert_conversation(
            context.tenant_id,
            context.user_id,
            context.conversation_id,
            final_title,
            current_timestamp(),
        )
        await usage_repo.record_usage(
            UsageRecord(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                message_id=context.message_id,
                tokens=None,
            )
        )

    async def stream(
        self,
        payload: dict[str, Any],
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> AsyncIterator[AnyStreamEvent]:
        tenant_id = get_current_tenant_id()
        user_id = get_current_user_id()
        conversation_id, messages, title, should_generate_title = (
            await self._prepare_conversation(
                payload,
                conversation_repo,
                tenant_id,
                user_id,
            )
        )
        await self._persist_incoming_messages(
            payload,
            message_repo,
            tenant_id,
            conversation_id,
            messages,
        )
        message_id, model_id, openai_messages = self._build_message_context(payload, messages)

        context = StreamContext(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_id=model_id,
            title=title,
            should_generate_title=should_generate_title,
            messages=messages,
            openai_messages=openai_messages,
            web_search=extract_web_search(payload),
        )

        return self._stream_with_persistence(
            context=context,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            usage_repo=usage_repo,
        )
