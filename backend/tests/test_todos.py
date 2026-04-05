"""TODO API tests."""

from fastapi.testclient import TestClient


class TestListTodos:
    def test_list_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/todos", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["todos"] == []

    def test_list_with_items(self, client: TestClient, auth_headers: dict):
        client.post("/api/v1/todos", json={"title": "Task 1"}, headers=auth_headers)
        client.post("/api/v1/todos", json={"title": "Task 2"}, headers=auth_headers)
        response = client.get("/api/v1/todos", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["todos"]) == 2

    def test_list_without_token(self, client: TestClient):
        response = client.get("/api/v1/todos")
        assert response.status_code == 403


class TestCreateTodo:
    def test_create_success(self, client: TestClient, auth_headers: dict):
        response = client.post("/api/v1/todos", json={"title": "Buy milk"}, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy milk"
        assert data["completed"] is False
        assert "todo_id" in data
        assert "created_at" in data

    def test_create_without_title(self, client: TestClient, auth_headers: dict):
        response = client.post("/api/v1/todos", json={}, headers=auth_headers)
        assert response.status_code == 422


class TestUpdateTodo:
    def test_update_title(self, client: TestClient, auth_headers: dict):
        create_resp = client.post("/api/v1/todos", json={"title": "Old title"}, headers=auth_headers)
        todo_id = create_resp.json()["todo_id"]

        response = client.patch(f"/api/v1/todos/{todo_id}", json={"title": "New title"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "New title"
        assert response.json()["completed"] is False

    def test_toggle_completed(self, client: TestClient, auth_headers: dict):
        create_resp = client.post("/api/v1/todos", json={"title": "Task"}, headers=auth_headers)
        todo_id = create_resp.json()["todo_id"]

        response = client.patch(f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_update_not_found(self, client: TestClient, auth_headers: dict):
        response = client.patch("/api/v1/todos/nonexistent-id", json={"title": "Updated"}, headers=auth_headers)
        assert response.status_code == 404


class TestDeleteTodo:
    def test_delete_success(self, client: TestClient, auth_headers: dict):
        create_resp = client.post("/api/v1/todos", json={"title": "To delete"}, headers=auth_headers)
        todo_id = create_resp.json()["todo_id"]

        response = client.delete(f"/api/v1/todos/{todo_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        list_resp = client.get("/api/v1/todos", headers=auth_headers)
        assert len(list_resp.json()["todos"]) == 0

    def test_delete_not_found(self, client: TestClient, auth_headers: dict):
        response = client.delete("/api/v1/todos/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
