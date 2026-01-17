def test_rag_streams(client):
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
    assert "data:" in response.text
    assert "rag" in response.text
