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


def test_rag_job_create_returns_worker_payload(client):
    response = client.post(
        "/api/rag/jobs",
        json={
            "query": "Create a longform outline.",
            "dataSource": "tool0101",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["jobId"].startswith("job-")
    assert body["conversationId"].startswith("conv-")
    worker_request = body["workerRequest"]
    assert worker_request["jobId"] == body["jobId"]
    assert worker_request["request"]["pipeline"] == "longform"
    assert worker_request["request"]["chatId"] == body["conversationId"]
    assert worker_request["request"]["dataSource"] == "tool0101"
    assert worker_request["user"] is not None


def test_rag_job_status_not_found(client):
    response = client.get("/api/rag/jobs/job-missing")
    assert response.status_code == 404


def test_rag_job_list_returns_items(client):
    first = client.post(
        "/api/rag/jobs",
        json={
            "query": "First longform job.",
            "dataSource": "tool0101",
        },
    )
    second = client.post(
        "/api/rag/jobs",
        json={
            "query": "Second longform job.",
            "dataSource": "tool0101",
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    first_id = first.json()["jobId"]
    second_id = second.json()["jobId"]

    response = client.get("/api/rag/jobs", params={"limit": 10})
    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]
    assert len(items) == 2
    returned_ids = {item["jobId"] for item in items}
    assert returned_ids == {first_id, second_id}
    assert payload["continuationToken"] is None
