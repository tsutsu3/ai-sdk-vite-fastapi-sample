def test_capabilities_response_shape(client):
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("models"), list)
    assert payload.get("models"), "expected at least one model"
    assert "defaultModel" in payload
    assert "apiPageSizes" in payload

    model_ids = {model.get("id") for model in payload["models"]}
    assert payload["defaultModel"] in model_ids
    api_page_sizes = payload["apiPageSizes"]
    assert "messagesPageSizeDefault" in api_page_sizes
    assert "messagesPageSizeMax" in api_page_sizes
    assert "conversationsPageSizeDefault" in api_page_sizes
    assert "conversationsPageSizeMax" in api_page_sizes
