from app.features.conversations.ports import ConversationRepository
from app.features.messages.models import MessagePartRecord, MessageRecord
from app.features.messages.ports import MessageRepository
from app.features.retrieval.run.models import (
    AuthContext,
    ConversationContext,
    ResponseContext,
    ToolContext,
)
from app.features.retrieval.run.utils import resolve_conversation_id
from app.features.retrieval.schemas import RetrievalQueryRequest
from app.features.title.utils import generate_fallback_title
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime
from app.shared.usage_metrics import compute_bytes_in, compute_bytes_out


class RetrievalPersistenceService:
    """Persist conversation metadata, messages, titles, and usage."""

    def __init__(
        self,
        *,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._usage_repo = usage_repo

    async def ensure_conversation(
        self,
        *,
        auth_ctx: AuthContext,
        payload: RetrievalQueryRequest,
        tool_ctx: ToolContext,
        user_message_text: str,
    ) -> ConversationContext:
        conversation_id = resolve_conversation_id(payload)
        existing = await self._conversation_repo.get_conversation(
            auth_ctx.tenant_id,
            auth_ctx.user_id,
            conversation_id,
        )
        title = existing.title if existing else DEFAULT_CHAT_TITLE
        should_generate_title = not title or title == DEFAULT_CHAT_TITLE
        await self._conversation_repo.upsert_conversation(
            auth_ctx.tenant_id,
            auth_ctx.user_id,
            conversation_id,
            title or DEFAULT_CHAT_TITLE,
            tool_id=tool_ctx.tool_id_for_conversation,
        )
        return ConversationContext(
            conversation_id=conversation_id,
            title=title or DEFAULT_CHAT_TITLE,
            should_generate_title=should_generate_title,
            user_message_text=user_message_text,
        )

    async def maybe_generate_title(
        self,
        *,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        conversation_ctx: ConversationContext,
        response_ctx: ResponseContext,
    ) -> str:
        if not conversation_ctx.should_generate_title or not conversation_ctx.user_message_text:
            return ""
        generated_title = generate_fallback_title(
            [
                MessageRecord(
                    id=response_ctx.message_id,
                    role="user",
                    parts=[
                        MessagePartRecord(type="text", text=conversation_ctx.user_message_text)
                    ],
                    created_at=now_datetime(),
                    parent_message_id="",
                )
            ]
        )
        if generated_title and generated_title != conversation_ctx.title:
            await self._conversation_repo.upsert_conversation(
                auth_ctx.tenant_id,
                auth_ctx.user_id,
                conversation_ctx.conversation_id,
                generated_title,
                tool_id=tool_ctx.tool_id_for_conversation,
            )
        return generated_title

    async def save_messages(
        self,
        *,
        auth_ctx: AuthContext,
        conversation_ctx: ConversationContext,
        response_ctx: ResponseContext,
        response_text: str,
    ) -> None:
        messages_to_upsert: list[MessageRecord] = []
        user_message_text = conversation_ctx.user_message_text
        if user_message_text:
            user_message_id = f"msg-{uuid4_str()}"
            messages_to_upsert.append(
                MessageRecord(
                    id=user_message_id,
                    role="user",
                    parts=[MessagePartRecord(type="text", text=user_message_text)],
                    created_at=now_datetime(),
                    parent_message_id="",
                )
            )
        if response_text:
            parent_message_id = messages_to_upsert[0].id if messages_to_upsert else ""
            messages_to_upsert.append(
                MessageRecord(
                    id=response_ctx.message_id,
                    role="assistant",
                    parts=[MessagePartRecord(type="text", text=response_text)],
                    created_at=now_datetime(),
                    parent_message_id=parent_message_id,
                    model_id=response_ctx.selected_model or None,
                )
            )
        if messages_to_upsert:
            await self._message_repo.upsert_messages(
                auth_ctx.tenant_id,
                auth_ctx.user_id,
                conversation_ctx.conversation_id,
                messages_to_upsert,
            )

    async def record_usage(
        self,
        *,
        auth_ctx: AuthContext,
        conversation_ctx: ConversationContext,
        response_ctx: ResponseContext,
        response_text: str,
    ) -> None:
        await self._usage_repo.record_usage(
            UsageRecord(
                tenant_id=auth_ctx.tenant_id,
                user_id=auth_ctx.user_id,
                conversation_id=conversation_ctx.conversation_id,
                message_id=response_ctx.message_id,
                model_id=response_ctx.selected_model or None,
                tokens_in=None,
                tokens_out=None,
                bytes_in=compute_bytes_in(response_ctx.request_payload),
                bytes_out=compute_bytes_out(response_text),
                requests=1,
            )
        )

    async def record_usage_entry(
        self,
        *,
        auth_ctx: AuthContext,
        conversation_ctx: ConversationContext,
        message_id: str,
        model_id: str | None,
        request_payload: list[dict[str, str]] | None,
        response_text: str | None,
    ) -> None:
        await self._usage_repo.record_usage(
            UsageRecord(
                tenant_id=auth_ctx.tenant_id,
                user_id=auth_ctx.user_id,
                conversation_id=conversation_ctx.conversation_id,
                message_id=message_id,
                model_id=model_id,
                tokens_in=None,
                tokens_out=None,
                bytes_in=compute_bytes_in(request_payload),
                bytes_out=compute_bytes_out(response_text),
                requests=1,
            )
        )


def uuid4_str() -> str:
    from uuid import uuid4

    return str(uuid4())
