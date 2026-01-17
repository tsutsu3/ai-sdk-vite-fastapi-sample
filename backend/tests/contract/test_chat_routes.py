def test_chat_stream_response_shape(client):
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


def test_chat_invalid_message_role(client):
    response = client.post(
        "/api/chat",
        json={
            "model": "fake-static",
            "messages": [
                {
                    "role": "invalid",
                    "parts": [{"type": "text", "text": "Hello"}],
                }
            ],
        },
    )
    assert response.status_code == 422


def test_chat_missing_messages(client):
    response = client.post(
        "/api/chat",
        json={"model": "fake-static"},
    )
    assert response.status_code == 422


def test_chat_empty_messages(client):
    response = client.post(
        "/api/chat",
        json={"model": "fake-static", "messages": []},
    )
    assert response.status_code == 400
