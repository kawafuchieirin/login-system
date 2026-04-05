"""Passkey endpoint tests."""


def test_registration_options_requires_auth(client):
    """Registration options require authentication."""
    response = client.post("/api/v1/passkey/register/options")
    assert response.status_code == 403


def test_registration_options_success(client, auth_headers):
    """Get registration options for authenticated user."""
    response = client.post("/api/v1/passkey/register/options", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "challenge" in data
    assert "rp" in data
    assert data["rp"]["id"] == "localhost"
    assert "user" in data


def test_list_credentials_empty(client, auth_headers):
    """List credentials returns empty list for new user."""
    response = client.get("/api/v1/passkey/credentials", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["credentials"] == []


def test_authentication_options_no_auth(client):
    """Authentication options do not require auth."""
    response = client.post(
        "/api/v1/passkey/authenticate/options",
        json={"email": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert "challenge" in data


def test_authentication_options_with_email(client, auth_headers):
    """Authentication options with specific email."""
    response = client.post(
        "/api/v1/passkey/authenticate/options",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    assert "challenge" in response.json()


def test_verify_registration_invalid_credential(client, auth_headers):
    """Verify registration with invalid credential fails."""
    response = client.post(
        "/api/v1/passkey/register/verify",
        headers=auth_headers,
        json={"credential": {"id": "invalid", "type": "public-key"}},
    )
    assert response.status_code == 400


def test_verify_authentication_invalid_credential(client):
    """Verify authentication with invalid credential fails."""
    response = client.post(
        "/api/v1/passkey/authenticate/verify",
        json={"credential": {"id": "invalid", "_challenge_user_id": "unknown"}},
    )
    assert response.status_code == 401


def test_delete_credential_not_found(client, auth_headers):
    """Delete non-existent credential returns 404."""
    response = client.delete(
        "/api/v1/passkey/credentials/nonexistent",
        headers=auth_headers,
    )
    assert response.status_code == 404
