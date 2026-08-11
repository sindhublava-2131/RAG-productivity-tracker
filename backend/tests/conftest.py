from __future__ import annotations

import os
from collections.abc import Generator

# Ensure the app runs in testing mode (lifespan skips migrations/seeding).
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import models
from database import Base, get_db
from main import app
from services.rag.embeddings import FakeEmbeddingService
from services.rag.pipeline import RagPipeline
from services.rag.providers.base import FakeLLMProvider
from services.rag.service import RagService, configure_rag_service, reset_rag_service
from services.rag.vector_store import InMemoryVectorStore


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_vector_store():
    return InMemoryVectorStore()


@pytest.fixture
def fake_embeddings():
    return FakeEmbeddingService()


@pytest.fixture
def fake_llm_provider():
    return FakeLLMProvider()


@pytest.fixture(autouse=True)
def rag_service(fake_vector_store, fake_embeddings, fake_llm_provider):
    pipeline = RagPipeline(
        vector_store=fake_vector_store,
        embeddings=fake_embeddings,
        llm_provider=fake_llm_provider,
    )
    service = RagService(
        vector_store=fake_vector_store,
        embeddings=fake_embeddings,
        pipeline=pipeline,
    )
    configure_rag_service(service)
    yield service
    reset_rag_service()


@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> models.User:
    user = models.User(
        name="Test User",
        email="testuser@example.com",
        password_hash=auth.get_password_hash("securepassword123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user) -> str:
    return auth.create_access_token(data={"sub": test_user.email})


@pytest.fixture
def auth_headers(user_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def second_user(db_session) -> models.User:
    user = models.User(
        name="Second User",
        email="seconduser@example.com",
        password_hash=auth.get_password_hash("securepassword456"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_headers(second_user) -> dict[str, str]:
    token = auth.create_access_token(data={"sub": second_user.email})
    return {"Authorization": f"Bearer {token}"}
