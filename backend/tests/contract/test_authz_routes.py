def test_authz_response_shape(client):
    response = client.get("/api/authz")
    assert response.status_code == 200
    payload = response.json()
    assert "user" in payload
    assert isinstance(payload.get("tools"), list)
    assert "toolGroups" in payload

    user = payload["user"]
    assert "id" in user
    assert "email" in user
    assert "provider" in user
    assert isinstance(payload["toolGroups"], list)
    if payload["toolGroups"]:
        group = payload["toolGroups"][0]
        assert "id" in group
        assert isinstance(group.get("items", []), list)
