import pytest

from app.features.conversations.service import ConversationService
from app.features.conversations.tenant_scoped import TenantScopedConversationRepository
from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)


@pytest.mark.asyncio
async def test_get_conversation_includes_messages():
    conversation_repo = TenantScopedConversationRepository(
        "default",
        MemoryConversationRepository(),
    )
    message_repo = MemoryMessageRepository()
    service = ConversationService(conversation_repo, message_repo)

    response = await service.get_conversation("user-1", "conv-quickstart")

    assert response is not None
    assert response.id == "conv-quickstart"
    assert len(response.messages) > 0
