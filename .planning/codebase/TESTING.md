# Testing Patterns

**Analysis Date:** 2026-08-11

## Test Framework

**Current state: No tests exist in this repository.**

- No `*.test.*` / `*.spec.*` files, no `tests/` directory, and no test runner configuration anywhere in the repo.
- Backend declares `pytest>=7.4.0` in `backend/requirements.txt` (line 11), but no pytest config (`pytest.ini`, `pyproject.toml`, `setup.cfg`) exists and there are no test modules under `backend/`.
- Frontend `frontend/package.json` has no test script and no test dependencies installed (`package-lock.json` contains no jest, vitest, or @testing-library packages).

**Recommended framework setup (matches existing stack):**

- **Backend:** `pytest` (already in `backend/requirements.txt`) with `fastapi.testclient.TestClient` for API-level tests. Add a `backend/tests/` directory with `backend/tests/conftest.py` that overrides the `get_db` dependency and creates an isolated SQLite database:
  ```python
  # backend/tests/conftest.py
  import pytest
  from fastapi.testclient import TestClient
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from database import Base, get_db
  import models
  import main

  TEST_DB = "sqlite:///./test_cozy.db"
  engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
  TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

  def override_get_db():
      db = TestingSession()
      try:
          yield db
      finally:
          db.close()

  main.app.dependency_overrides[get_db] = override_get_db

  @pytest.fixture()
  def client():
      Base.metadata.create_all(bind=engine)
      with TestClient(main.app) as c:
          yield c
      Base.metadata.drop_all(bind=engine)
  ```
- **Frontend:** add `vitest` + `@testing-library/react` + `@testing-library/jest-dom` as devDependencies and a `"test": "vitest"` script. Vitest works with the existing `frontend/vite.config.ts` (add a `test` block to it). No jsdom setup exists yet.

**Run Commands (once configured):**
```bash
cd backend; pytest                          # Run all backend tests
cd backend; pytest tests/test_tasks.py -k complete   # Single test file / keyword
cd frontend; npm test                      # Run all frontend tests (vitest)
cd frontend; npm run test -- --coverage    # Frontend coverage
```

## Test File Organization

**Current state:** None.

**Recommended layout:**
```
backend/
├── tests/
│   ├── conftest.py            # TestClient fixture + get_db override (see above)
│   ├── test_auth.py           # register / login / me
│   ├── test_tasks.py          # CRUD + complete endpoint
│   ├── test_analytics.py      # metric computation
│   └── test_rag.py            # format_task_memory + evaluator (pure functions)
frontend/
└── src/
    ├── App.test.tsx
    └── components/
        ├── TaskManager.test.tsx
        ├── AuthModal.test.tsx
        └── services/api.test.ts   # mock axios adapter, fallback behavior
```

**Naming:** `test_*.py` for Python (pytest discovery default); `*.test.tsx` co-located with the component for frontend (Vitest default glob).

## Test Structure

**No existing suites to model from.** Follow these patterns aligned with the codebase:

**Backend — API tests exercise the real router stack:**
```python
# backend/tests/test_auth.py
def test_register_and_login(client):
    res = client.post("/api/auth/register", json={
        "name": "Test User", "email": "t@example.com", "password": "secret1"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token

    res = client.post("/api/auth/login", json={
        "email": "t@example.com", "password": "secret1"
    })
    assert res.status_code == 200

def test_duplicate_email_returns_400(client):
    payload = {"name": "A", "email": "dup@example.com", "password": "secret1"}
    assert client.post("/api/auth/register", json=payload).status_code == 200
    assert client.post("/api/auth/register", json=payload).status_code == 400
```

**Backend — pure-function tests for the RAG service** (`backend/rag_service.py` needs no DB or network):
```python
# backend/tests/test_rag.py
from rag_service import format_task_memory, EvaluatorAgent

def test_format_task_memory_complete():
    text = format_task_memory("COMPLETE", {
        "title": "DB Lab", "priority": "HIGH",
        "estimated_minutes": 60, "actual_minutes": 45, "due_date": None
    })
    assert "Completed 'DB Lab'" in text
    assert "15 minutes faster" in text

def test_evaluator_filters_low_relevance():
    mems = [{"relevance_score": 0.05}, {"relevance_score": 0.9}]
    valid, score = EvaluatorAgent.evaluate("q", mems)
    assert valid[0]["relevance_score"] == 0.9
```

**Frontend — component render + interaction with @testing-library/react:**
```tsx
// frontend/src/components/TaskManager.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskManager } from './TaskManager';

test('renders task title', () => {
  render(<TaskManager tasks={[]} onTaskChange={() => {}} />);
  expect(screen.getByText(/No tasks found/i)).toBeInTheDocument();
});
```

**Patterns:**
- Backend: use the `client` fixture; assert `status_code` then payload shape against the Pydantic response fields (`backend/schemas.py`).
- Protected endpoints (everything except `POST /api/auth/register` and `POST /api/auth/login`) require `Authorization: Bearer <token>` — register/login first in the test, or use a helper that reuses the token.
- Frontend: mock `frontend/src/services/api.ts` service objects with `vi.mock()` so components render in isolation.

## Mocking

**Framework:** None installed. Use `pytest` fixtures/monkeypatch on the backend; `vi.mock` + `vi.fn` (Vitest) on the frontend.

**Patterns:**
- Backend: the `get_db` dependency override in `backend/tests/conftest.py` (shown above) is the standard FastAPI mocking point — `main.app.dependency_overrides[get_db] = override_get_db`.
- `backend/rag_service.py` guards ChromaDB/SentenceTransformers behind a `try/except` at import (lines 35–47) and sets `CHROMA_AVAILABLE = False` with an `in_memory_docs` fallback (lines 49–50). Tests that must not touch ChromaDB or the network should force the fallback path (e.g., `monkeypatch.setattr(rag_service, "CHROMA_AVAILABLE", False)`). LLM provider calls in `MultiLLMQueryAgent.query` (`backend/rag_service.py:241-314`) hit real HTTP endpoints — always mock `requests.post` or force the `_generate_smart_fallback` path.
- Frontend: mock the axios layer or the service objects. `frontend/src/services/api.ts` already returns mock data on request failure — a test can trigger fallback by having the mocked axios reject, or better, use `vi.mock('../services/api')` to stub service methods directly:
  ```tsx
  vi.mock('../services/api', () => ({
    TaskService: { getTasks: vi.fn().mockResolvedValue([]), /* ... */ },
  }));
  ```

**What to Mock:**
- All external LLM providers (Ollama, OpenAI, Gemini, Grok) and ChromaDB persistence.
- `datetime.utcnow()`-dependent logic (`backend/main.py` seeding, `backend/routes/task_routes.py` `completed_at`) — freeze time with `monkeypatch` or `freezegun`.
- Frontend axios instance and browser `localStorage` (`cozy_token` key in `frontend/src/services/api.ts`).

**What NOT to Mock:**
- Pydantic schema validation and FastAPI route wiring (they are the code under test).
- `format_task_memory`, `EvaluatorAgent.evaluate`, analytics math in `backend/routes/analytics_routes.py` — these are pure and should run for real.
- React component rendering — use testing-library queries rather than shallow-render mocks.

## Fixtures and Factories

**Test Data:** None exists. The backend has a built-in demo seed in `backend/main.py` (lines 34–133) creating user `demo@cozy.app` and 5 tasks — do not depend on it in tests; create isolated data per test via the API or the SQLAlchemy session.

**Recommended fixture:**
```python
@pytest.fixture()
def auth_headers(client):
    client.post("/api/auth/register", json={"name": "U", "email": "u@x.com", "password": "secret1"})
    token = client.post("/api/auth/login", json={"email": "u@x.com", "password": "secret1"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Location:** `backend/tests/conftest.py`; frontend test data inline per test or in `frontend/src/test/fixtures.ts`.

## Coverage

**Requirements:** None enforced — no coverage tooling or CI gate exists.

**View Coverage (once vitest/pytest-cov added):**
```bash
cd backend; pip install pytest-cov; pytest --cov=. --cov-report=term-missing
cd frontend; npm run test -- --coverage
```

## Test Types

**Unit Tests:** Not used yet. Highest-value targets are the pure functions: `format_task_memory`, `EvaluatorAgent.evaluate`, `RetrievalAgent.retrieve` fallback path (`backend/rag_service.py`), and `auth.get_password_hash`/`verify_password`/`create_access_token` (`backend/auth.py`).

**Integration Tests:** Not used yet. Use FastAPI `TestClient` against the real routers + SQLite to cover the full request path: auth → create task → complete task → analytics. The `get_db` override in `conftest.py` makes this isolated from the dev database `cozy_productivity.db` (created via `DATABASE_URL` default in `backend/database.py:7`).

**E2E Tests:** Not used. No Playwright/Cypress dependency exists. If added, cover the Vite dev proxy (`frontend/vite.config.ts` `/api` → `localhost:8000`) and the docker-compose deployment.

## Common Patterns

**Async Testing:** Not applicable to backend — all route handlers are synchronous `def` (FastAPI runs them in a threadpool); call them synchronously through `TestClient`. Frontend tests should use `await screen.findBy*` for state updates after `handleAsk`/`fetchAnalytics` promises resolve (e.g., `AIAssistant.tsx` loading→response transition).

**Error Testing:**
```python
def test_delete_missing_task_returns_404(client, auth_headers):
    res = client.delete("/api/tasks/9999", headers=auth_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "Task not found"
```
The `"Task not found"` detail is repeated in `backend/routes/task_routes.py` (lines 69, 124, 152) — assert on it as the contract.

---

*Testing analysis: 2026-08-11*
