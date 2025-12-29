def test_rag_query_stream_shape(client):
    response = client.post(
        "/api/rag/query",
        json={
            "query": "hello",
            "dataSource": "rag01",
            "provider": "memory",
            "topK": 1,
        },
    )
    assert response.status_code == 200
    body = response.text
    assert "rag" in body
    assert "data:" in body
