from datetime import datetime, timezone

from app.features.conversations.models import (
    ConversationMetadata,
    ConversationResponse,
)
from app.features.conversations.repository.conversation_repository import (
    ConversationRepository,
)


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._conversation_store = {
            "conv-quickstart": {
                "id": "conv-quickstart",
                "title": "Project kickoff chat",
                "updatedAt": current_timestamp(),
                "messages": [
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
                ],
            },
            "conv-rag": {
                "id": "conv-rag",
                "title": "RAG tuning ideas",
                "updatedAt": current_timestamp(),
                "messages": [
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
                ],
            },
        }

    def list_conversations(self) -> list[ConversationMetadata]:
        return [
            ConversationMetadata(
                id=conv["id"],
                title=conv.get("title") or "Conversation",
                updatedAt=conv.get("updatedAt") or current_timestamp(),
            )
            for conv in self._conversation_store.values()
        ]

    def get_conversation(self, conversation_id: str) -> ConversationResponse | None:
        conversation = self._conversation_store.get(conversation_id)
        if not conversation:
            return None
        return ConversationResponse(
            id=conversation["id"],
            title=conversation.get("title") or "Conversation",
            updatedAt=conversation.get("updatedAt") or current_timestamp(),
            messages=conversation.get("messages", []),
        )
