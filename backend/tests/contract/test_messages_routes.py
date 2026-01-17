def test_messages_list_response_shape(client):
    response = client.get("/api/conversations/conv-quickstart/messages")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("messages"), list)
    assert "continuationToken" in payload


def test_messages_list_invalid_limit(client):
    response = client.get(
        "/api/conversations/conv-quickstart/messages",
        params={"limit": 0},
    )
    assert response.status_code == 422


def test_messages_list_conversation_not_found(client):
    response = client.get("/api/conversations/conv-not-exist/messages")
    assert response.status_code == 404


def test_update_message_reaction_invalid_value(client):
    response = client.patch(
        "/api/conversations/conv-quickstart/messages/msg-missing",
        json={"reaction": "love"},
    )
    assert response.status_code == 422


def test_update_message_reaction_not_found(client):
    response = client.patch(
        "/api/conversations/conv-quickstart/messages/msg-missing",
        json={"reaction": "like"},
    )
    assert response.status_code == 404
