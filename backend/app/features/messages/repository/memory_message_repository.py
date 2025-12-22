from app.features.messages.models import ChatMessage, MessagePart
from app.features.messages.ports import MessageRepository


class MemoryMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], list[ChatMessage]] = {}
        self._store[("default", "conv-quickstart")] = [
            ChatMessage(
                id="msg-system",
                role="system",
                parts=[MessagePart(type="text", text="You are a helpful project assistant.")],
            ),
            ChatMessage(
                id="msg-user-1",
                role="user",
                parts=[
                    MessagePart(
                        type="text",
                        text="Please outline the next steps for our AI SDK demo.",
                    )
                ],
            ),
            ChatMessage(
                id="msg-assistant-1",
                role="assistant",
                parts=[
                    MessagePart(
                        type="text",
                        text="Sure! I will list the milestones and owners so you can start quickly.",
                    )
                ],
            ),
        ]
        self._store[("default", "conv-rag")] = [
            ChatMessage(
                id="msg-user-2",
                role="user",
                parts=[
                    MessagePart(
                        type="text",
                        text="How can we improve retrieval quality for the docs index?",
                    )
                ],
            ),
            ChatMessage(
                id="msg-assistant-2",
                role="assistant",
                parts=[
                    MessagePart(
                        type="text",
                        text="Consider adding hierarchical chunking and reranking with a cross-encoder.",
                    )
                ],
            ),
        ]

    async def list_messages(self, tenant_id: str, conversation_id: str) -> list[ChatMessage]:
        return list(self._store.get((tenant_id, conversation_id), []))

    async def upsert_messages(
        self,
        tenant_id: str,
        conversation_id: str,
        messages: list[ChatMessage],
    ) -> None:
        self._store[(tenant_id, conversation_id)] = list(messages)

    async def delete_messages(self, tenant_id: str, conversation_id: str) -> None:
        self._store.pop((tenant_id, conversation_id), None)
