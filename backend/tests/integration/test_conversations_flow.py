import json


def _extract_conversation_id(body: str) -> str | None:
    for line in body.splitlines():
        if not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ").strip()
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "data-conversation":
            continue
        data = event.get("data") or {}
        conv_id = data.get("convId")
        if isinstance(conv_id, str) and conv_id:
            return conv_id
    return None


def test_archive_and_list_archived_conversations(client):
    chat = client.post(
        "/api/chat",
        json={
            "model": "fake-static",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Archive this"}],
                }
            ],
        },
    )
    assert chat.status_code == 200
    conversation_id = _extract_conversation_id(chat.text)
    assert conversation_id

    update = client.patch(
        f"/api/conversations/{conversation_id}",
        json={"archived": True},
    )
    assert update.status_code == 200
    assert update.json().get("archived") is True

    archived = client.get("/api/conversations", params={"archived": True})
    assert archived.status_code == 200
    archived_ids = {item.get("id") for item in archived.json().get("conversations", [])}
    assert conversation_id in archived_ids
