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


def test_chat_streams_and_persists(client):
    response = client.post(
        "/api/chat",
        json={
            "model": "fake-static",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello"}],
                }
            ],
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("x-vercel-ai-protocol") == "data"
        or response.headers.get("x-vercel-ai-ui-message-stream") == "v1"
    )
    body = response.text
    assert "data:" in body

    conversation_id = _extract_conversation_id(body)
    assert conversation_id
    messages_response = client.get(f"/api/conversations/{conversation_id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json().get("messages", [])
    assert len(messages) >= 1


def test_conversations_list_includes_new_chat(client):
    response = client.post(
        "/api/chat",
        json={
            "model": "fake-static",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Ping"}],
                }
            ],
        },
    )
    conversation_id = _extract_conversation_id(response.text)
    assert conversation_id
    response = client.get("/api/conversations")
    assert response.status_code == 200
    conversations = response.json().get("conversations", [])
    assert any(item.get("id") == conversation_id for item in conversations)
