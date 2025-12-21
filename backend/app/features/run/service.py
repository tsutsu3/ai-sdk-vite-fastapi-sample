import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from app.features.chat.streamers import ChatStreamer, sse
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.run.models import StreamContext
from app.features.title.title_generator import TitleGenerator
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.request_context import get_current_tenant_id, get_current_user_id


def extract_messages(payload: dict[str, Any]) -> list[dict]:
    messages = payload.get("messages")
    if isinstance(messages, list):
        return [message for message in messages if isinstance(message, dict)]
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


def to_openai_messages(messages: list[dict]) -> list[dict]:
    converted = []
    for message in messages:
        role = message.get("role")
        parts = message.get("parts")
        if not role or not isinstance(parts, list):
            continue
        text_parts = [
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        content = " ".join(part.strip() for part in text_parts if part).strip()
        if content:
            converted.append({"role": role, "content": content})
    return converted


class RunService:
    def __init__(
        self,
        streamer: ChatStreamer,
        title_generator: TitleGenerator,
    ) -> None:
        self._streamer = streamer
        self._title_generator = title_generator

    async def _prepare_conversation(
        self,
        payload: dict[str, Any],
        conversation_repo: ConversationRepository,
        tenant_id: str,
        user_id: str,
    ) -> tuple[str, list[dict], str, bool]:
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
        messages: list[dict],
    ) -> None:
        file_ids = extract_file_ids(payload)
        if file_ids and messages:
            messages[-1].setdefault("metadata", {})["fileIds"] = file_ids
        await message_repo.upsert_messages(tenant_id, conversation_id, messages)

    def _build_message_context(
        self,
        payload: dict[str, Any],
        messages: list[dict],
    ) -> tuple[str, str | None, list[dict]]:
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
    ) -> str:
        await conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            generated,
            current_timestamp(),
        )
        return sse({"type": "data-title", "data": {"title": generated}})

    async def _stream_with_persistence(
        self,
        *,
        context: StreamContext,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> AsyncIterator[str]:
        response_text = ""
        final_title = context.title
        title_task: asyncio.Task[str] | None = None
        if context.should_generate_title:
            title_task = asyncio.create_task(self._title_generator.generate(context.messages))
        title_sent = False
        try:
            async for delta in self._streamer.stream_chat(
                context.openai_messages, context.model_id
            ):
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
        assistant_message = {
            "id": context.message_id,
            "role": "assistant",
            "parts": [{"type": "text", "text": response_text}],
        }
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
    ) -> AsyncIterator[str]:
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
        )

        return self._stream_with_persistence(
            context=context,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            usage_repo=usage_repo,
        )
