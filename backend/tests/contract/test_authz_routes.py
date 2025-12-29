def test_authz_response_shape(client):
    response = client.get("/api/authz")
    assert response.status_code == 200
    payload = response.json()
    assert "user" in payload
    assert isinstance(payload.get("tools"), list)
    assert "toolGroups" in payload
