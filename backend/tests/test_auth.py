from __future__ import annotations

from datetime import timedelta

import auth


def test_register_user(client):
    payload = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "strongpassword123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"


def test_register_duplicate_email(client, test_user):
    payload = {
        "name": "Duplicate User",
        "email": test_user.email,
        "password": "anotherpassword123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "securepassword123",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_user.email


def test_login_wrong_password(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "wrongpassword123",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_unauthenticated_protected_endpoint(client):
    response = client.get("/api/tasks")
    assert response.status_code == 401


def test_invalid_token(client):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = client.get("/api/tasks", headers=headers)
    assert response.status_code == 401


def test_expired_token(client, test_user):
    expired_token = auth.create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(seconds=-10),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/tasks", headers=headers)
    assert response.status_code == 401


def test_get_current_user_profile(client, auth_headers, test_user):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name
