<!-- refreshed: 2026-08-11 -->
# Architecture

**Analysis Date:** 2026-08-11

## System Overview

Two-tier web application: a React SPA (Vite + Tailwind) frontend and a FastAPI backend that combines a SQL CRUD API with a grounded RAG memory pipeline. No server-side rendering; the frontend proxies all `/api` calls to the backend during dev (Vite proxy) and nginx reverse-proxies them in Docker.

```text
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend (React SPA)                       │
│  `frontend/src/App.tsx` — tab router & global state              │
│  ├── CuteHeader.tsx        ├── TaskManager.tsx                  │
│  ├── AuthModal.tsx         ├── AnalyticsDashboard.tsx           │
│  └── AIAssistant.tsx        (`frontend/src/components/`)        │
│  Services: `frontend/src/services/api.ts` (axios + interceptors) │
├──────────────────────────────┬──────────────────────────────────┤
│  Dev: Vite proxy `/api` → 8000 (vite.config.ts)                 │
│  Prod: nginx reverse-proxy `/api` → backend:8000 (nginx.conf)   │
└──────────────────────────────▼──────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  `backend/main.py` — app factory, lifespan, routers, middleware  │
│  Routers (`backend/routes/`):                                    │
│    health_routes | auth_routes | task_routes                     │
│    | analytics_routes | rag_routes                               │
│  ├── Config: `backend/core/config.py` (pydantic-settings)        │
│  ├── ORM: `backend/models.py`, `backend/database.py`             │
│  ├── Auth: `backend/auth.py` (PyJWT + bcrypt)                    │
│  ├── Migrations: `backend/alembic/`                              │
│  └── RAG subsystem: `backend/services/rag/` (package)            │
└───────────────┬───────────────────────────────┬──────────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│  SQLite (dev) / PostgreSQL  │   │  ChromaDB vector store          │
│  `DATABASE_URL` (env)       │   │  + SentenceTransformers         │
│  users + tasks tables       │   │  (`backend/chroma_db/`)         │
└─────────────────────────────┘   └─────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| App root | Tab navigation, user/task/analytics state, auth modal lifecycle, 401 handling | `frontend/src/App.tsx` |
| Services | All HTTP to backend; token injection; 401 interceptor; typed `ApiError` | `frontend/src/services/api.ts` |
| Shared types | Mirrors backend Pydantic response shapes | `frontend/src/types.ts` |
| FastAPI app factory | Config, CORS, request-context middleware, router registration, lifespan (schema + demo seed) | `backend/main.py` |
| Settings | Single typed settings object (pydantic-settings), env-driven | `backend/core/config.py` |
| DB session layer | Engine, session factory, declarative Base, `get_db` dependency | `backend/database.py` |
| ORM models | `users` and `tasks` (strict 2-table schema) | `backend/models.py` |
| Pydantic schemas | Request/response validation + enums (`Priority`, `Status`, `TaskAction`) | `backend/schemas.py` |
| Auth helpers | bcrypt hashing, JWT encode/decode, `get_current_user` dependency | `backend/auth.py` |
| Auth routes | Register, login, current-user profile | `backend/routes/auth_routes.py` |
| Task routes | CRUD + lifecycle → RAG memory emission | `backend/routes/task_routes.py` |
| Analytics routes | 11 productivity metrics computed in-memory | `backend/routes/analytics_routes.py` |
| RAG routes | `/api/rag/query`, `/api/rag/memories`, memory delete | `backend/routes/rag_routes.py` |
| Health routes | `/health/live`, `/health/ready` | `backend/routes/health_routes.py` |
| RAG service root | Composition root; lazy wiring; singleton + test injection | `backend/services/rag/service.py` |
| RAG pipeline | retrieval → rerank → context → generate → validate | `backend/services/rag/pipeline.py` |

## Pattern Overview

**Overall:** Layered client-server monolith with a service facade on the frontend and thin router + service-package structure on the backend.

**Key Characteristics:**
- Backend follows FastAPI idioms: routers in `backend/routes/`, dependency-injected DB sessions via `Depends(get_db)`, Pydantic schemas for I/O boundaries, `Depends(auth.get_current_user)` for protected routes
- RAG subsystem is a proper package (`backend/services/rag/`) with clear single-responsibility modules: `retrieval.py`, `reranking.py`, `context.py`, `grounding.py`, `embeddings.py`, `memory.py`, `vector_store.py`, `pipeline.py`, plus a `providers/` package for LLM backends
- All RAG components depend on abstractions (`VectorStore`, `EmbeddingService`, `LLMProvider`) enabling full offline test fakes (`InMemoryVectorStore`, `FakeEmbeddingService`, `FakeLLMProvider`)
- Frontend service layer (`frontend/src/services/api.ts`) no longer mocks on error — real `ApiError`s propagate to components (the previous mock-fallback engine was removed)
- No framework-level state management (no Redux/Zustand); state lives in `App.tsx` via `useState` and is passed down as props; tab components fetch their own data

## Layers

**Frontend Presentation Layer:**
- Purpose: Render UI and handle user interaction
- Location: `frontend/src/components/`
- Contains: Presentational + container components (`CuteHeader.tsx`, `TaskManager.tsx`, `AnalyticsDashboard.tsx`, `AIAssistant.tsx`, `AuthModal.tsx`)
- Depends on: `frontend/src/services/api.ts`, `frontend/src/types.ts`
- Used by: `frontend/src/App.tsx`

**Frontend Service Layer:**
- Purpose: Centralize HTTP calls, JWT injection, typed error handling
- Location: `frontend/src/services/api.ts`
- Contains: axios instance with request/response interceptors, `ApiError`, `setUnauthorizedHandler`, and `AuthService` / `TaskService` / `AnalyticsService` / `RAGService`
- Depends on: axios, `frontend/src/types.ts`
- Used by: `App.tsx` and all components

**Backend API Layer (routers):**
- Purpose: Expose REST endpoints, validate input, call ORM/service logic
- Location: `backend/routes/`
- Contains: `health_routes.py`, `auth_routes.py`, `task_routes.py`, `analytics_routes.py`, `rag_routes.py`
- Depends on: `backend/models.py`, `backend/schemas.py`, `backend/auth.py`, `backend/database.py`, `backend/services/rag/*`
- Used by: `backend/main.py`

**Backend Service Layer:**
- Purpose: Business logic, persistence, and the RAG pipeline
- Location: `backend/services/rag/` (RAG package) + root modules (`auth.py`, `database.py`, `models.py`, `schemas.py`, `core/config.py`)
- Depends on: SQLAlchemy, ChromaDB, SentenceTransformers, external LLM APIs
- Used by: `backend/routes/`

**Data Layer:**
- Purpose: Durable state — relational + vector
- Location: SQLite file `backend/cozy_productivity.db` (dev) / PostgreSQL 16 (prod via `docker-compose.yml`), ChromaDB dir `backend/chroma_db/`
- Managed by: `backend/database.py`, `backend/services/rag/vector_store.py`

## Data Flow

### Primary Request Path (e.g., task list)

1. `App.tsx` / `TaskManager.tsx` calls `TaskService.getTasks()` (`frontend/src/services/api.ts`)
2. axios request interceptor injects `Authorization: Bearer <cozy_token>` from `localStorage` (`frontend/src/services/api.ts`)
3. Dev server proxies `/api` to `http://localhost:8000` via `frontend/vite.config.ts`; in Docker, nginx serves the SPA and proxies `/api` → `backend:8000` (`frontend/nginx.conf`)
4. `task_routes.get_tasks` runs, guarded by `Depends(auth.get_current_user)` → `backend/auth.py` decodes JWT, loads user from DB
5. SQLAlchemy query filters by `current_user.id`, ordered by `created_at desc` (`backend/routes/task_routes.py`)
6. Result serialized via `schemas.TaskResponse` and returned; on any error the service throws `ApiError` (surfaced by components)

### Task CRUD → RAG Memory Flow

1. `create_task` / `update_task` / `complete_task` / `delete_task` in `backend/routes/task_routes.py` commit the ORM change
2. After commit, the route calls `format_task_memory(action, task_data)` from `backend/services/rag/memory.py` to produce a natural-language sentence (CREATE / UPDATE / COMPLETE / DELAY / DELETE / OVERDUE)
3. `_persist_memory` calls `rag.store_memory_from_task(...)` → `MemoryIngestionService.build_memory` + `store` (`backend/services/rag/memory.py`), which embeds the text and adds it to the per-user ChromaDB collection `user_{user_id}_memories` (`backend/services/rag/vector_store.py`); memory ids use `uuid4` (no collision risk)
4. Memory failures raise `MemoryIngestionError`, caught and logged by the route — the task op still succeeds (see CONCERNS.md)
5. Optional startup seeding in `backend/main.py` lifespan creates demo user/tasks/memories when `SEED_DEMO` is on (non-production only)

### RAG Query Flow (Grounded Pipeline)

1. `AIAssistant.tsx` sends question + provider to `RAGService.queryAssistant` → `POST /api/rag/query` (`backend/routes/rag_routes.py`)
2. `RagPipeline.run()` (`backend/services/rag/pipeline.py`) executes:
   - **Retrieval:** `HybridRetriever.retrieve(user_id, query, top_k)` — user-scoped ChromaDB semantic search combined with lexical token overlap (weighted `lexical_weight = 0.3`); mandatory `user_id` metadata filter (`backend/services/rag/retrieval.py`)
   - **Rerank:** `Reranker.rerank(candidates, threshold, limit)` — deterministic 4-factor score (semantic 0.5 / lexical 0.25 / metadata 0.15 / 30-day recency decay 0.1); filters below `RAG_RELEVANCE_THRESHOLD` (0.25) (`backend/services/rag/reranking.py`)
   - **Context:** `ContextBuilder.build(ranked)` — deduplicates by source id, caps at `RAG_MAX_SOURCES` (5) and `RAG_MAX_CONTEXT_CHARS` (4000) (`backend/services/rag/context.py`)
   - **Generate:** `llm.complete(system_prompt, user_prompt)` with a hardcoded grounded system prompt (memories marked UNTRUSTED, citation format `[Source: <id>]` mandated); provider resolved via `get_provider()` registry; `asyncio.wait_for` timeout; LLM failure yields a graceful "unavailable" answer (`backend/services/rag/pipeline.py`)
   - **Validate:** `GroundingValidator.validate(answer, sources)` — rejects hallucinated source ids; grounded only if ≥1 valid citation and no invalid ones (`backend/services/rag/grounding.py`)
3. Response assembles `answer`, `sources`, `confidence`, `grounded`, `retrieval_count`, `provider`, `model`, `execution_time_ms` (`backend/schemas.py` RAGQueryResponse)

### Auth Flow

1. `AuthModal.tsx` → `AuthService.login/register` → `POST /api/auth/login` (`auth_routes.py`)
2. bcrypt verify via `auth.verify_password` (`backend/auth.py`); JWT created with `sub` = email, 7-day expiry
3. Token stored in `localStorage['cozy_token']`; attached to all subsequent requests by the axios interceptor; a 401 response clears the token and triggers `setUnauthorizedHandler` → `App.tsx` resets state and reopens the auth modal

**State Management:**
- Frontend: local `useState` in `App.tsx` (`user`, `tasks`, `analytics`, `activeTab`); children receive props + `onTaskChange`/`onSuccess` callbacks; `AnalyticsDashboard` and `AIAssistant` fetch their own data
- Backend: stateless; per-request DB session via `get_db` dependency; JWT is the only session mechanism; auth token valid 7 days
- Vector store: per-user ChromaDB collections keyed by `user_{user_id}_memories`

## Key Abstractions

**Service objects (frontend):**
- Purpose: Group related API calls per domain
- Examples: `AuthService`, `TaskService`, `AnalyticsService`, `RAGService` — all in `frontend/src/services/api.ts`
- Pattern: Plain exported objects of async methods; each converts errors to typed `ApiError` and throws

**RagService composition root (backend):**
- Purpose: Lazy-wire embeddings, vector store, memory service, and pipeline; process-wide singleton
- Example: `RagService` + `get_rag_service()` / `configure_rag_service()` / `reset_rag_service()` in `backend/services/rag/service.py`
- Pattern: Constructor injection of optional components; lazy property creation on first use so importing never downloads models or opens ChromaDB; tests inject fakes

**VectorStore interface:**
- Purpose: Abstract persistent, user-scoped vector persistence
- Example: `VectorStore` ABC with `add`/`update`/`delete`/`search`/`get_by_id`/`list_by_user`/`count`; implementations `ChromaVectorStore` (persistent) and `InMemoryVectorStore` (`backend/services/rag/vector_store.py`)
- Pattern: Application logic depends only on the interface

**LLMProvider interface:**
- Purpose: Abstract multi-provider LLM calls
- Example: `LLMProvider` ABC with `complete(system_prompt, user_prompt)`; `OllamaProvider`, `OpenAIProvider`, `GeminiProvider`, `GrokProvider`, plus `FakeLLMProvider`/`FailingLLMProvider` for tests (`backend/services/rag/providers/`)
- Pattern: Factory registry `get_provider()`; every provider raises `LLMError` on failure

**Dependency-injected DB session:**
- Purpose: Provide a request-scoped SQLAlchemy session to route handlers
- Example: `get_db` in `backend/database.py`, consumed as `db: Session = Depends(get_db)`
- Pattern: FastAPI generator dependency with `yield`/`finally: db.close()`

**Current-user dependency:**
- Purpose: Resolve the authenticated user from the Bearer token for every protected route
- Example: `get_current_user` in `backend/auth.py`, consumed as `current_user: models.User = Depends(auth.get_current_user)`
- Pattern: FastAPI dependency chaining

**Props-interface components (frontend):**
- Purpose: Type component contracts
- Example: `interface Props { tasks: Task[]; onTaskChange: () => void; }` in `frontend/src/components/TaskManager.tsx`
- Pattern: Local `Props` interface per component; named `export const X: React.FC<Props>`

## Entry Points

**Backend:**
- Location: `backend/main.py`
- Invocation: `uvicorn main:app --reload --port 8000` (dev) or `CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]` (`backend/Dockerfile`)
- Responsibilities: Create FastAPI app (`APP_NAME`/`APP_VERSION` 2.1.0 from settings), CORS middleware, request-context middleware (`X-Request-Id`, latency logging), include 5 routers, lifespan handler (production: rely on Alembic; dev: `Base.metadata.create_all` + optional demo seed), serve `GET /` root info
- Also `python start.py` at repo root launches backend + frontend together (used in dev)

**Frontend:**
- Location: `frontend/src/main.tsx` → `frontend/src/App.tsx`
- Invocation: `npm run dev` (Vite dev server on port 3000) or `docker compose up --build` (nginx serving `frontend/dist/`)
- Responsibilities: Mount React app into `#root`; `App.tsx` owns top-level state and tab routing between `tasks` | `analytics` | `assistant`

## Architectural Constraints

- **Threading:** FastAPI app on uvicorn; route handlers are synchronous `def` (FastAPI runs them in a threadpool); RAG query route is `async def` and the LLM call is genuinely async (httpx) with `asyncio.wait_for` timeout — no blocking HTTP in the event loop
- **SQLite:** requires `check_same_thread: False` (`backend/database.py`); SQLite strips tzinfo from `DateTime(timezone=True)` — `_aware()`/`_parse_iso()` helpers re-attach UTC (`backend/routes/analytics_routes.py`, `backend/routes/rag_routes.py`)
- **Global state:** module-level `_rag_service` singleton (`backend/services/rag/service.py`); browser `cozy_token` in `localStorage` is the client-side session store
- **Circular imports:** none detected — `main.py` imports routes; routes import `models`, `schemas`, `auth`, `database`, `services.rag.*`; no module imports `main.py`
- **DB access style:** SQLAlchemy 2.0 `Mapped`/`mapped_column` typed models; queries use `db.query(Model).filter(...)` ORM style; no repository layer
- **Migrations:** Alembic manages production schema (`backend/alembic/versions/0001_initial.py`); dev uses `create_all` convenience path in the lifespan
- **Three-service deployment:** `docker-compose.yml` defines `db` (PostgreSQL 16), `backend` (port 8000), `frontend` (port 3000→80); ChromaDB persisted via named volume `chroma_data`
- **Demo data:** `SEED_DEMO` gates demo seeding and is only honored when `APP_ENV != production` — but `docker-compose.yml` sets `SEED_DEMO=true` (see CONCERNS.md)

## Anti-Patterns

### Silent Vector-Store Degradation

**What happens:** If ChromaDB init fails, `ChromaVectorStore` transparently uses an `InMemoryVectorStore` (`backend/services/rag/vector_store.py`) — memories are "stored" but are volatile and lost on restart.
**Why it's wrong:** Data-loss with no user-visible signal; a long-running degraded deployment silently forgets task history.
**Do this instead:** Surface store status via health/logs; fail closed with a clear error when persistence is unavailable, or persist the fallback to disk.

### Best-Effort Memory Persistence

**What happens:** `_persist_memory` in `backend/routes/task_routes.py` catches `MemoryIngestionError` and only logs it — the task operation still reports success.
**Why it's wrong:** Relational DB and vector store can diverge; the AI assistant silently misses events.
**Do this instead:** Make memory writes transactional with the task write, or expose a consistency indicator/retry mechanism.

### Hardcoded Production Secret in Compose

**What happens:** `docker-compose.yml` sets `JWT_SECRET_KEY=cozy_rag_productivity_tracker_super_secret_key_2026`.
**Why it's wrong:** Anyone with the repo can forge valid JWTs for any deployment that uses the compose defaults; combined with `SEED_DEMO=true`, the published demo account is a backdoor.
**Do this instead:** Read the secret from a `.env`/secret store; remove the hardcoded value and the demo seed from the production compose file.

## Error Handling

**Strategy:** Typed exceptions on the backend; defensive UI handling on the frontend.

**Patterns:**
- FastAPI `HTTPException` for expected errors: duplicate email → 400 (`auth_routes.py`), bad credentials → 401 with `WWW-Authenticate` (`auth_routes.py`), missing task → 404 (`task_routes.py`), empty question → 400 (`rag_routes.py`)
- `MemoryIngestionError` for vector-store persistence failures (`backend/services/rag/memory.py`)
- `LLMError` for provider call failures, with retry/backoff in `_http.py`; pipeline converts failures to a graceful "unavailable" answer with `confidence=0` and `grounded=False`
- `GroundingValidator` rejects hallucinated citations
- Frontend: every service method converts errors to `ApiError` (status + detail) and throws; `AuthModal.tsx` and `AIAssistant.tsx` display `error.message`; `App.tsx` catches load failures and resets to empty state
- Startup seeding wrapped in try/except with rollback (`backend/main.py`)

## Cross-Cutting Concerns

**Logging:** stdlib `logging` configured in `backend/main.py` (`LOG_LEVEL` from settings) with named loggers; request-context middleware logs every request with `request_id` and latency. No structured logging / log aggregation.

**Validation:** Pydantic v2 schemas in `backend/schemas.py`; enums for `Priority`/`Status`/`TaskAction` (strictly validated, so invalid values are rejected at the boundary); `EmailStr` for emails; length/range constraints on fields; `RAGQueryRequest` question capped at 2000 chars.

**Authentication:** JWT (HS256) with bcrypt hashing (`backend/auth.py`); `OAuth2PasswordBearer`; every route except auth/health/root requires `Depends(auth.get_current_user)`; frontend stores token in `localStorage` and injects via axios interceptor; 401 response auto-clears the session.

---

*Architecture analysis: 2026-08-11*
