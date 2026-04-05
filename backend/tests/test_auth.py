"""Authentication API tests."""

from fastapi.testclient import TestClient


class TestRegister:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "user_id" in data
        assert "created_at" in data

    def test_register_duplicate_email(self, client: TestClient):
        client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password123"})
        response = client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "password456"})
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"

    def test_register_short_password(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "short"},
        )
        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient):
        client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "password123"})
        response = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        client.post("/api/v1/auth/register", json={"email": "wrong@example.com", "password": "password123"})
        response = client.post("/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrongpass"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post("/api/v1/auth/login", json={"email": "none@example.com", "password": "password123"})
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_without_token(self, client: TestClient):
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 403


class TestMe:
    def test_me_success(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "user_id" in data

    def test_me_without_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_me_invalid_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401


class TestHealthCheck:
    def test_health(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
