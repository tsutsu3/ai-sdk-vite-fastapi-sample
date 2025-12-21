from app.features.messages.ports import MessageRepository


class MemoryMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], list[dict]] = {}
        self._store[("default", "conv-quickstart")] = [
            {
                "id": "msg-system",
                "role": "system",
                "parts": [
                    {
                        "type": "text",
                        "text": "You are a helpful project assistant.",
                    }
                ],
            },
            {
                "id": "msg-user-1",
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Please outline the next steps for our AI SDK demo.",
                    }
                ],
            },
            {
                "id": "msg-assistant-1",
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Sure! I will list the milestones and owners so you can start quickly.",
                    }
                ],
            },
        ]
        self._store[("default", "conv-rag")] = [
            {
                "id": "msg-user-2",
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "How can we improve retrieval quality for the docs index?",
                    }
                ],
            },
            {
                "id": "msg-assistant-2",
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Consider adding hierarchical chunking and reranking with a cross-encoder.",
                    }
                ],
            },
        ]

    async def list_messages(self, tenant_id: str, conversation_id: str) -> list[dict]:
        return list(self._store.get((tenant_id, conversation_id), []))

    async def upsert_messages(
        self,
        tenant_id: str,
        conversation_id: str,
        messages: list[dict],
    ) -> None:
        self._store[(tenant_id, conversation_id)] = list(messages)

    async def delete_messages(self, tenant_id: str, conversation_id: str) -> None:
        self._store.pop((tenant_id, conversation_id), None)
