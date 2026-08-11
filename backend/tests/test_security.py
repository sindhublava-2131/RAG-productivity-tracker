from __future__ import annotations

from datetime import timedelta

import pytest

import auth
from core.config import Settings
from core.rate_limit import is_allowed, reset_limits
from services.rag.context import SourceBlock
from services.rag.grounding import GroundingValidator
from services.rag.vector_store import VectorRecord


def test_jwt_tampering(client, user_token):
    tampered_token = user_token[:-4] + "abcd"
    response = client.get("/api/tasks", headers={"Authorization": f"Bearer {tampered_token}"})
    assert response.status_code == 401


def test_missing_jwt(client):
    response = client.get("/api/tasks")
    assert response.status_code == 401


def test_expired_jwt(client, test_user):
    expired_token = auth.create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(seconds=-5),
    )
    response = client.get("/api/tasks", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_cross_user_memory_access(client, auth_headers, second_user_headers, rag_service):
    # User 1 creates memory
    mem_id = rag_service.store_memory_from_task(
        user_id=1,
        task_id=99,
        action="CREATE",
        content="User 1 private memory",
    )

    # User 2 tries to list/delete User 1's memory
    res_list = client.get("/api/rag/memories", headers=second_user_headers)
    assert res_list.status_code == 200
    items = res_list.json()["items"]
    user2_mem_ids = [item["id"] for item in items]
    assert mem_id not in user2_mem_ids

    res_del = client.delete(f"/api/rag/memories/{mem_id}", headers=second_user_headers)
    assert res_del.status_code == 404


def test_malformed_rag_request(client, auth_headers):
    response = client.post("/api/rag/query", json={"question": ""}, headers=auth_headers)
    assert response.status_code in (400, 422)


def test_oversized_rag_input(client, auth_headers):
    oversized_q = "a" * 2500
    response = client.post("/api/rag/query", json={"question": oversized_q}, headers=auth_headers)
    assert response.status_code == 422  # Pydantic max_length validation


def test_invalid_provider_handling(client, auth_headers):
    response = client.post(
        "/api/rag/query",
        json={"question": "Test query", "provider": "nonexistent_provider"},
        headers=auth_headers,
    )
    # The pipeline catches unknown provider and falls back safely to default provider
    assert response.status_code == 200


def test_invalid_citation_rejected():
    validator = GroundingValidator()
    sources = [SourceBlock(VectorRecord(id="valid_1", text="valid memory text", metadata={}))]
    result = validator.validate("Answering using fake [Source: hallucinated_99]", sources)
    assert result.grounded is False
    assert "hallucinated_99" in result.invalid_source_ids


from pydantic import ValidationError


def test_production_requires_jwt_secret():
    with pytest.raises((ValueError, ValidationError)):
        s = Settings(APP_ENV="production", JWT_SECRET_KEY="")
        s.resolved_jwt_secret()


def test_secrets_not_logged(caplog):
    secret_key = "super-secret-jwt-key-never-log-me"
    s = Settings(JWT_SECRET_KEY=secret_key)
    sec = s.resolved_jwt_secret()
    assert secret_key not in caplog.text
    assert sec == secret_key


def test_logout_revokes_token(client, auth_headers, user_token):
    # Before logout, the token is valid.
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200

    # Logout revokes it server-side.
    res = client.post("/api/auth/logout", headers=auth_headers)
    assert res.status_code == 200

    # The same token is now rejected.
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 401
    assert user_token is not None


def test_change_password_flow(client, auth_headers, test_user):
    # Wrong current password is rejected.
    res = client.post(
        "/api/auth/change-password",
        json={"current_password": "wrongpass", "new_password": "newsecure123"},
        headers=auth_headers,
    )
    assert res.status_code == 401

    # Correct current password succeeds.
    res = client.post(
        "/api/auth/change-password",
        json={"current_password": "securepassword123", "new_password": "newsecure123"},
        headers=auth_headers,
    )
    assert res.status_code == 200

    # Old password no longer works; new one does.
    old_login = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "securepassword123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "newsecure123"},
    )
    assert new_login.status_code == 200


def test_model_allowlist_rejects_unknown_models(client, auth_headers):
    # Unknown model for a cloud provider is rejected before reaching the LLM.
    res = client.post(
        "/api/rag/query",
        json={"question": "hello", "provider": "openai", "model_name": "gpt-9999"},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "not allowed" in res.json()["detail"].lower()


def test_rate_limiter_enforces_limit():
    reset_limits()
    bucket = "test-bucket:1.2.3.4"
    assert is_allowed(bucket, limit=3, window_seconds=60) is True
    assert is_allowed(bucket, limit=3, window_seconds=60) is True
    assert is_allowed(bucket, limit=3, window_seconds=60) is True
    assert is_allowed(bucket, limit=3, window_seconds=60) is False
    reset_limits()
