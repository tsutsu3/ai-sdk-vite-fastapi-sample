from typing import Any

from app.features.chat.run.message_utils import extract_conversation_id
from app.features.chat.run.models import RunRequest, StreamContext
from app.features.conversations.ports import ConversationRepository
from app.features.messages.models import MessagePartRecord, MessageRecord
from app.features.messages.ports import MessageRepository
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime
from app.shared.usage_metrics import compute_bytes_in, compute_bytes_out


class PersistenceService:
    """Handle conversation, message, and usage persistence.

    This service encapsulates all repository writes for the run flow:
    it prepares conversation state, persists message history, updates
    conversation metadata (including titles), and records usage metrics.
    It returns no events and performs no LLM execution logic.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._usage_repo = usage_repo

    async def prepare_conversation(
        self,
        payload: RunRequest,
        tenant_id: str,
        user_id: str,
    ) -> tuple[str, list[MessageRecord], str, bool]:
        """Ensure conversation exists and return its current state."""
        conversation_id = extract_conversation_id(payload)
        messages, _ = await self._message_repo.list_messages(
            tenant_id,
            user_id,
            conversation_id,
            limit=None,
            continuation_token=None,
            descending=False,
        )
        existing = await self._conversation_repo.get_conversation(
            tenant_id,
            user_id,
            conversation_id,
        )
        title = existing.title if existing else DEFAULT_CHAT_TITLE
        should_generate_title = not title or title == DEFAULT_CHAT_TITLE
        await self._conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            title,
            tool_id="chat",
        )
        return conversation_id, messages, title, should_generate_title

    async def save_title(
        self,
        *,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> None:
        """Persist the updated conversation title."""
        await self._conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            title,
            tool_id="chat",
        )

    async def save_messages(self, context: StreamContext, response_text: str) -> None:
        """Persist the user and assistant messages."""
        assistant_message = self._build_assistant_message(context, response_text)
        if context.messages or assistant_message:
            messages_to_upsert = list(context.messages)
            if assistant_message:
                messages_to_upsert.append(assistant_message)
            await self._message_repo.upsert_messages(
                context.tenant_id,
                context.user_id,
                context.conversation_id,
                messages_to_upsert,
            )

    async def save_conversation_final(
        self,
        *,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        final_title: str,
    ) -> None:
        """Persist final conversation metadata after streaming finishes."""
        await self._conversation_repo.upsert_conversation(
            tenant_id,
            user_id,
            conversation_id,
            final_title,
            tool_id="chat",
        )

    async def record_usage(
        self,
        context: StreamContext,
        request_payload: list[dict[str, Any]],
        response_text: str,
    ) -> None:
        """Record usage metrics for the run."""
        await self._usage_repo.record_usage(
            UsageRecord(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                message_id=context.message_id,
                model_id=context.model_id,
                tokens_in=None,
                tokens_out=None,
                # Count payload sizes for usage metrics.
                bytes_in=compute_bytes_in(request_payload),
                bytes_out=compute_bytes_out(response_text),
                requests=1,
            )
        )

    @staticmethod
    def _build_assistant_message(
        context: StreamContext,
        response_text: str,
    ) -> MessageRecord | None:
        """Build the assistant message for persistence."""
        if not response_text:
            return None
        parent_message_id = ""
        for message in reversed(context.messages):
            if message.role == "user":
                parent_message_id = message.id
                break
        return MessageRecord(
            id=context.message_id,
            role="assistant",
            parts=[MessagePartRecord(type="text", text=response_text)],
            created_at=now_datetime(),
            parent_message_id=parent_message_id,
            model_id=context.model_id,
        )
