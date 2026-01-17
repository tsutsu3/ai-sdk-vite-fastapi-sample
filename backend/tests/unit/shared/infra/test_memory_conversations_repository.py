import pytest

from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)


@pytest.mark.asyncio
async def test_archive_and_list_conversations():
    repo = MemoryConversationRepository()
    tenant_id = "tenant-1"
    user_id = "user-1"

    active, _ = await repo.list_conversations(tenant_id, user_id)
    assert active

    target = active[0]
    await repo.archive_conversation(
        tenant_id,
        user_id,
        target.id,
        archived=True,
    )

    active_after, _ = await repo.list_conversations(tenant_id, user_id)
    archived_after, _ = await repo.list_archived_conversations(tenant_id, user_id)

    assert all(item.id != target.id for item in active_after)
    assert any(item.id == target.id for item in archived_after)
