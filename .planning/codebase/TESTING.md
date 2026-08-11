# Testing Patterns

**Analysis Date:** 2026-08-11

## Test Framework

**Backend: pytest (~8.3.0, dev extra in `backend/pyproject.toml`)**
- Config in `backend/pyproject.toml`: `[tool.pytest.ini_options] testpaths = ["tests"]`, `addopts = "-q"`; `pytest-cov` available as dev extra
- API tests use `fastapi.testclient.TestClient` against the real router stack with dependency overrides
- RAG tests run **fully offline** against fakes (`InMemoryVectorStore`, `FakeEmbeddingService`, `FakeLLMProvider`) — no network, no model downloads, no disk writes
- Run: `cd backend && pytest` (or `python -m pytest`)

**Frontend: vitest (~1.6.0) + @testing-library/react + jsdom**
- Config lives in `frontend/vite.config.ts` `test` block: `environment: 'jsdom'`, `globals: true`, `setupFiles: ['./src/test/setup.ts']`, `css: false`
- Scripts in `frontend/package.json`: `test` (`vitest run`), `test:watch`, `test:coverage`, plus `lint`/`typecheck`/`build`
- Run: `cd frontend && npm test`

**CI:** `.github/workflows/ci.yml` runs `ruff`, `mypy`, `pytest` (backend); `eslint`, `tsc --noEmit`, `vitest run`, `build` (frontend); plus a Docker Compose smoke test.

## Test File Organization

**Backend (`backend/tests/`):**
```
backend/tests/
├── conftest.py                     # Shared fixtures (client, db_session, fakes, auth)
├── fixtures/
│   └── rag/
│       └── evaluation_dataset.py   # 8-case deterministic RAG benchmark dataset
├── test_auth.py                    # register / login / me / token edge cases
├── test_tasks.py                   # CRUD + complete + cross-user isolation
├── test_analytics.py               # 11 metrics incl. empty-user edge case
├── test_health.py                  # liveness / readiness / root
├── test_rag.py                     # pipeline, retrieval, rerank, grounding, benchmark, injection defense
├── test_security.py                # JWT tampering/expiry, cross-user memory, oversized input, prod secret
└── __init__.py
```

**Frontend (co-located):**
```
frontend/src/services/api.test.ts        # AuthService/TaskService/RAGService with mocked axios
frontend/src/components/AIAssistant.test.tsx  # render, ask, grounded answer, error state
frontend/src/test/setup.ts               # jest-dom matchers, cleanup, localStorage reset, mock restore
```

**Naming:** `test_*.py` (pytest discovery), `*.test.ts(x)` co-located (vitest glob).

## Test Structure

**Backend — API tests exercise the real router stack via the `client` fixture:**
```python
# backend/tests/test_auth.py
def test_register_user(client):
    payload = {"name": "New User", "email": "newuser@example.com", "password": "strongpassword123"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
```

**Backend — pure/unit tests for RAG components with fakes (no DB/network):**
```python
# backend/tests/test_rag.py
def test_metadata_filtering(fake_vector_store, fake_embeddings):
    retriever = HybridRetriever(fake_vector_store, fake_embeddings, top_k=5)
    # ...seed records, filter by action=COMPLETE, assert only the matching one returns
```

**Backend — async pipeline tests** use `pytest.mark.asyncio` (e.g., `test_empty_retrieval_and_insufficient_context`, `test_llm_failure`).

**Frontend — component render + interaction with @testing-library/react:**
```tsx
// frontend/src/components/AIAssistant.test.tsx
vi.mock('../services/api', () => ({ RAGService: { queryAssistant: vi.fn(), getMemories: vi.fn() } }));
// render, type into the input, fire Enter, waitFor grounded answer, assert chips/sources
```

**Patterns:**
- Backend: assert `status_code`, then payload shape against Pydantic response fields (`backend/schemas.py`).
- Protected endpoints require `Authorization: Bearer <token>` — use the `auth_headers` fixture.
- Frontend: `vi.mock('../services/api')` isolates components; `waitFor`/`findBy*` for async state updates.
- Async RAG tests assert `grounded`/`confidence`/`answer` contract plus system-prompt injection-defense invariant (`_GROUNDED_SYSTEM_PROMPT` contains "UNTRUSTED reference data").

## Mocking

**Backend:**
- `backend/tests/conftest.py` overrides `get_db` on `main.app` (`app.dependency_overrides[get_db] = ...`) with an in-memory SQLite engine (`StaticPool`, `check_same_thread: False`), creating/dropping schema per test.
- RAG fakes are first-class: `fake_vector_store` (`InMemoryVectorStore`), `fake_embeddings` (`FakeEmbeddingService`, deterministic 8-dim vectors), `fake_llm_provider` (`FakeLLMProvider` / `FailingLLMProvider`).
- The **autouse** `rag_service` fixture builds a `RagPipeline` + `RagService` from fakes and installs it via `configure_rag_service(service)`, resetting via `reset_rag_service()` after each test — so route-level tests hit the fake pipeline, never ChromaDB or real LLMs.
- Security tests validate real `auth` module behavior (JWT signing/expiry/tampering) against the PyJWT/bcrypt implementation.
- `test_production_requires_jwt_secret` constructs `Settings(APP_ENV="production", JWT_SECRET_KEY="")` directly to assert the fail-fast validator.

**Frontend:**
- `frontend/src/services/api.test.ts` mocks the `axios` module with `vi.mock` (mock instance with `get/post/put/patch/delete` + interceptors), then asserts token storage, error → `ApiError` conversion, and provider payloads.
- `frontend/src/components/AIAssistant.test.tsx` mocks `../services/api` service objects directly with `vi.fn()`.
- `frontend/src/test/setup.ts` runs `cleanup()`, `localStorage.clear()`, and `vi.restoreAllMocks()` after each test.

**What to Mock:** All external LLM providers, ChromaDB persistence, embedding model downloads, the axios HTTP layer.
**What NOT to Mock:** Pydantic schema validation, FastAPI route wiring, `format_task_memory`, reranker/grounding math, analytics metric computation, JWT/bcrypt crypto.

## Fixtures and Factories

**`backend/tests/conftest.py` provides:**
- `db_engine` — in-memory SQLite engine (StaticPool); `db_session` — sessionmaker-backed session
- `fake_vector_store`, `fake_embeddings`, `fake_llm_provider` — RAG fakes
- `rag_service` (autouse) — installs the fake-backed `RagService` singleton
- `client` — `TestClient` with `get_db` overridden to `db_session`
- `test_user` + `user_token` + `auth_headers` — seeded user and bearer header
- `second_user` + `second_user_headers` — second tenant for cross-user isolation tests

**Test data:** `backend/tests/fixtures/rag/evaluation_dataset.py` — 8 benchmark cases (`EVALUATION_DATASET`) covering exact lookup, semantic lookup, recency, completed-task lookup, irrelevant filtering, multiple-relevant, empty history, and ambiguous queries, each with `min_precision`/`min_recall` thresholds. `test_rag_evaluation_dataset_benchmark` runs them and asserts aggregate `avg_precision >= 0.7`, `avg_recall >= 0.8`.

**Do NOT depend on the dev demo seed** (`SEED_DEMO` in `backend/main.py`) in tests — create isolated data via the API or the SQLAlchemy session.

## Coverage

- `pytest-cov` is a dev extra; `npm run test:coverage` exists on the frontend.
- No hard coverage gate in CI today.
- View coverage: `cd backend && pytest --cov=. --cov-report=term-missing` and `cd frontend && npm run test:coverage`.

## Test Types

**Unit Tests:** `test_rag.py` pure-component tests (retrieval, reranking, context dedup/limit, grounding validation), `test_security.py` crypto/validator tests.

**Integration Tests:** API-level suites via `client` — auth flows (`test_auth.py`), task CRUD + completion + cross-user 404s (`test_tasks.py`), analytics metrics with seeded rows (`test_analytics.py`), health endpoints (`test_health.py`), RAG endpoints with fake pipeline (`test_security.py` cross-user memory access, `test_rag.py` benchmark).

**E2E Tests:** Not present as a dedicated suite. CI `docker-smoke-test` job covers deployment-level verification (compose up, `/health/ready` polling, register → create task → complete → RAG query via curl).

## Common Patterns

**Async Testing:** RAG pipeline tests use `pytest.mark.asyncio` (asyncio mode is available since the app is `async def` for the RAG query route). All other route handlers are sync `def` and are tested synchronously via `TestClient`. Frontend tests use `await waitFor(...)` / `findBy*` for post-promise UI updates.

**Error Testing:**
```python
# backend/tests/test_security.py
def test_missing_jwt(client):
    response = client.get("/api/tasks")
    assert response.status_code == 401

def test_cross_user_memory_access(client, auth_headers, second_user_headers, rag_service):
    # user 1 stores a memory; user 2 cannot list or delete it (404)
```

**Known gaps (see CONCERNS.md):** no frontend tests for `TaskManager.tsx`, `AuthModal.tsx`, `AnalyticsDashboard.tsx`, or `CuteHeader.tsx`; no coverage gate; no E2E (Playwright/Cypress) suite.

---

*Testing analysis: 2026-08-11*
