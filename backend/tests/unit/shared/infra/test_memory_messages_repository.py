import pytest

from app.features.messages.models import MessagePartRecord, MessageRecord
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)


@pytest.mark.asyncio
async def test_upsert_and_delete_messages():
    repo = MemoryMessageRepository()
    tenant_id = "tenant-1"
    user_id = "user-1"
    conversation_id = "conv-1"
    messages = [
        MessageRecord(id="m1", role="user", parts=[MessagePartRecord(type="text", text="hi")])
    ]

    stored = await repo.upsert_messages(tenant_id, user_id, conversation_id, messages)
    assert len(stored) == 1
    stored, _ = await repo.list_messages(tenant_id, user_id, conversation_id)
    assert len(stored) == 1

    await repo.delete_messages(tenant_id, user_id, conversation_id)
    cleared, _ = await repo.list_messages(tenant_id, user_id, conversation_id)
    assert cleared == []
