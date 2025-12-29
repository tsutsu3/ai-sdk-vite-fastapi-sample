def test_conversations_list_response_shape(client):
    response = client.get("/api/conversations")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("conversations"), list)
    assert payload["conversations"], "expected at least one conversation"
    sample = payload["conversations"][0]
    assert "id" in sample
    assert "title" in sample
    assert "updatedAt" in sample


def test_messages_list_response_shape(client):
    response = client.get("/api/conversations/conv-quickstart/messages")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("messages"), list)
