from __future__ import annotations


def test_create_task(client, auth_headers):
    payload = {
        "title": "Study RAG Architecture",
        "description": "Read papers and build prototype",
        "priority": "HIGH",
        "estimated_minutes": 60,
    }
    response = client.post("/api/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Study RAG Architecture"
    assert data["priority"] == "HIGH"
    assert data["status"] == "PENDING"
    assert data["estimated_minutes"] == 60


def test_list_tasks(client, auth_headers):
    payload1 = {"title": "Task 1", "priority": "LOW"}
    payload2 = {"title": "Task 2", "priority": "HIGH"}
    client.post("/api/tasks", json=payload1, headers=auth_headers)
    client.post("/api/tasks", json=payload2, headers=auth_headers)

    response = client.get("/api/tasks", headers=auth_headers)
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2


def test_get_task(client, auth_headers):
    create_res = client.post("/api/tasks", json={"title": "Specific Task"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Task"


def test_update_task(client, auth_headers):
    create_res = client.post("/api/tasks", json={"title": "Old Title"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    update_payload = {"title": "New Title", "priority": "URGENT"}
    response = client.put(f"/api/tasks/{task_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["priority"] == "URGENT"


def test_complete_task(client, auth_headers):
    create_res = client.post("/api/tasks", json={"title": "Task to complete", "estimated_minutes": 30}, headers=auth_headers)
    task_id = create_res.json()["id"]

    response = client.put(f"/api/tasks/{task_id}/complete?actual_minutes=25", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["actual_minutes"] == 25
    assert data["completed_at"] is not None


def test_delete_task(client, auth_headers):
    create_res = client.post("/api/tasks", json={"title": "Task to delete"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200

    get_res = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_missing_task(client, auth_headers):
    response = client.get("/api/tasks/99999", headers=auth_headers)
    assert response.status_code == 404


def test_unauthorized_task_access(client):
    response = client.get("/api/tasks/1")
    assert response.status_code == 401


def test_cross_user_task_access(client, auth_headers, second_user_headers):
    create_res = client.post("/api/tasks", json={"title": "User 1 Secret Task"}, headers=auth_headers)
    task_id = create_res.json()["id"]

    # User 2 tries to access User 1's task
    get_res = client.get(f"/api/tasks/{task_id}", headers=second_user_headers)
    assert get_res.status_code == 404

    # User 2 tries to update User 1's task
    put_res = client.put(f"/api/tasks/{task_id}", json={"title": "Hacked"}, headers=second_user_headers)
    assert put_res.status_code == 404

    # User 2 tries to complete User 1's task
    complete_res = client.put(f"/api/tasks/{task_id}/complete", headers=second_user_headers)
    assert complete_res.status_code == 404

    # User 2 tries to delete User 1's task
    del_res = client.delete(f"/api/tasks/{task_id}", headers=second_user_headers)
    assert del_res.status_code == 404
