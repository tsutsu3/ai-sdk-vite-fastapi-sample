def test_rag_query_stream_shape(client):
    response = client.post(
        "/api/rag/query",
        json={
            "query": "hello",
            "dataSource": "tool01",
            "provider": "memory",
            "model": "fake-static",
            "topK": 1,
        },
    )
    assert response.status_code == 200
    assert response.headers.get("x-vercel-ai-protocol") == "data"
    body = response.text
    assert "rag" in body
    assert "data:" in body


def test_rag_query_missing_query(client):
    response = client.post(
        "/api/rag/query",
        json={
            "dataSource": "tool01",
            "provider": "memory",
            "model": "fake-static",
        },
    )
    assert response.status_code == 422


def test_rag_query_invalid_provider(client):
    response = client.post(
        "/api/rag/query",
        json={
            "query": "hello",
            "dataSource": "tool01",
            "provider": "unknown-provider",
            "model": "fake-static",
            "topK": 1,
        },
    )
    assert response.status_code == 422
