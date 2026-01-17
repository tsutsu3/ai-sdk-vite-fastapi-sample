def test_health_response_shape(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
