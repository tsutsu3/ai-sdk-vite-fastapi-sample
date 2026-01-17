import pytest


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
    assert "archived" in sample
    assert "continuationToken" in payload


def test_conversation_detail_response_shape(client):
    response = client.get("/api/conversations/conv-quickstart")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("id") == "conv-quickstart"
    assert isinstance(payload.get("messages"), list)
    assert "title" in payload
    assert "updatedAt" in payload


def test_update_conversation_title(client):
    response = client.patch(
        "/api/conversations/conv-quickstart",
        json={"title": "Updated title"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("title") == "Updated title"


def test_archive_conversation(client):
    response = client.patch(
        "/api/conversations/conv-quickstart",
        json={"archived": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("archived") is True


def test_bulk_archive_conversations(client):
    response = client.patch("/api/conversations", json={"archived": True})
    assert response.status_code == 200
    payload = response.json()
    conversations = payload.get("conversations", [])
    assert conversations
    assert all(conv.get("archived") is True for conv in conversations)


def test_delete_conversation(client):
    response = client.delete("/api/conversations/conv-quickstart")
    assert response.status_code == 204
    response = client.get("/api/conversations/conv-quickstart")
    assert response.status_code == 404


def test_delete_all_conversations(client):
    response = client.delete("/api/conversations")
    assert response.status_code == 204
    response = client.get("/api/conversations")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("conversations") == []


def test_conversations_list_pagination(client):
    response = client.get("/api/conversations", params={"limit": 1})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload.get("conversations", [])) == 1
    assert payload.get("continuationToken") == "1"


# https://docs.pydantic.dev/2.0/usage/types/booleans/
@pytest.mark.parametrize(
    "valid_body",
    [
        {"archived": "true"},
        {"archived": "True"},
        {"archived": "TRUE"},
        {"archived": "t"},
        {"archived": 1},
        {"archived": "1"},
        {"archived": "yes"},
        {"archived": "y"},
    ],
)
def test_update_conversation_valid_body(client, valid_body):
    response = client.patch(
        "/api/conversations/conv-quickstart",
        json=valid_body,
    )
    assert response.status_code == 200


def test_conversations_list_invalid_limit(client):
    response = client.get("/api/conversations", params={"limit": 0})
    assert response.status_code == 422


def test_get_conversation_not_found(client):
    response = client.get("/api/conversations/conv-not-exist")
    assert response.status_code == 404


def test_update_conversation_not_found(client):
    response = client.patch(
        "/api/conversations/conv-not-exist",
        json={"title": "Updated title"},
    )
    assert response.status_code == 404


def test_delete_conversation_not_found(client):
    response = client.delete("/api/conversations/conv-not-exist")
    assert response.status_code == 404


def test_conversations_list_negative_limit(client):
    response = client.get("/api/conversations", params={"limit": -1})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_body",
    [
        {"title": 123},
        {"archived": "true2"},
        {"title": "valid", "archived": "invalid"},
    ],
)
def test_update_conversation_invalid_body(client, invalid_body):
    response = client.patch(
        "/api/conversations/conv-quickstart",
        json=invalid_body,
    )
    assert response.status_code == 422


def test_bulk_update_conversations_invalid_field(client):
    response = client.patch("/api/conversations", json={"invalid_field": True})
    assert response.status_code == 400
