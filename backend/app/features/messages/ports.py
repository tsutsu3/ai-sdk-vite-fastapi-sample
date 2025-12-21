from typing import Protocol


class MessageRepository(Protocol):
    async def list_messages(self, tenant_id: str, conversation_id: str) -> list[dict]:
        """Return messages in raw ai-sdk format."""
        raise NotImplementedError

    async def upsert_messages(
        self,
        tenant_id: str,
        conversation_id: str,
        messages: list[dict],
    ) -> None:
        """Replace messages for the conversation."""
        raise NotImplementedError

    async def delete_messages(self, tenant_id: str, conversation_id: str) -> None:
        """Delete messages for the conversation."""
        raise NotImplementedError
