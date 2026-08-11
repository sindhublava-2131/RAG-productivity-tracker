<!-- refreshed: 2026-08-11 -->
# Architecture

**Analysis Date:** 2026-08-11

## System Overview

Two-tier web application: a React SPA (Vite + Tailwind) frontend and a FastAPI backend that combines a SQL CRUD API with a multi-agent RAG memory pipeline. No server-side rendering; the frontend proxies all `/api` calls to the backend during dev and is served as static files by nginx in Docker.

```text
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend (React SPA)                       │
│  App.tsx ─ tab router & global state                             │
│  ├── CuteHeader.tsx      ├── TaskManager.tsx                     │
│  ├── AuthModal.tsx       ├── AnalyticsDashboard.tsx              │
│  └── AIAssistant.tsx                                             │
│  `frontend/src/components/`                                      │
├─────────────────────────────────────────────────────────────────┤
│                       Services Layer                             │
│  `frontend/src/services/api.ts` (axios + mock fallback)          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP /api/* (JWT Bearer)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  `backend/main.py` app factory + router registration             │
│  Routes: auth_routes | task_routes | analytics_routes            │
│          | rag_routes   (`backend/routes/`)                      │
│  ├── SQLAlchemy ORM (`backend/models.py`, `database.py`)         │
│  └── RAG Pipeline  (`backend/rag_service.py`)                    │
└───────────────┬────────────────────────────────┬─────────────────┘
                │                                │
                ▼                                ▼
┌─────────────────────────────┐   ┌─────────────────────────────────┐
│  SQLite / PostgreSQL        │   │  ChromaDB vector store          │
│  `DATABASE_URL` (env)       │   │  + SentenceTransformers         │
│  Users, Tasks tables        │   │  (`backend/chroma_db/`)         │
└─────────────────────────────┘   └─────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| App root | Tab navigation, user/task/analytics state, auth modal lifecycle | `frontend/src/App.tsx` |
| Services | All HTTP to backend + in-browser mock fallback when API unavailable | `frontend/src/services/api.ts` |
| Shared types | Mirrors backend Pydantic response shapes | `frontend/src/types.ts` |
| FastAPI app factory | CORS, router registration, DB table creation, demo seeding | `backend/main.py` |
| DB session layer | Engine, session factory, declarative Base, `get_db` dependency | `backend/database.py` |
| ORM models | `users` and `tasks` (strict 2-table schema) | `backend/models.py` |
| Pydantic schemas | Request/response validation for all routes | `backend/schemas.py` |
| Auth helpers | bcrypt hashing, JWT encode/decode, `get_current_user` dependency | `backend/auth.py` |
| Auth routes | Register, login, current-user profile | `backend/routes/auth_routes.py` |
| Task routes | CRUD + lifecycle→RAG memory emission | `backend/routes/task_routes.py` |
| Analytics routes | 11 productivity metrics computed in-memory | `backend/routes/analytics_routes.py` |
| RAG routes | `/api/rag/query` and `/api/rag/memories` | `backend/routes/rag_routes.py` |
| RAG pipeline | Memory formatting, ChromaDB storage, 3-agent pipeline | `backend/rag_service.py` |

## Pattern Overview

**Overall:** Layered client-server monolith with a service facade on the frontend and thin router + service-module structure on the backend.

**Key Characteristics:**
- Backend follows FastAPI idioms: routers in `backend/routes/`, dependency-injected DB sessions via `Depends(get_db)`, Pydantic schemas for I/O boundaries
- RAG pipeline is implemented as module-level classes with static methods (agent classes) orchestrated by a module-level `run_rag_pipeline()` function
- Frontend uses a single service module (`frontend/src/services/api.ts`) exposing four exported service objects; every service method falls back to in-memory mock data on any API error, so the SPA renders standalone without the backend
- No framework-level state management (no Redux/Zustand); state lives in `App.tsx` via `useState` and is passed down as props; tab components fetch their own data directly from services

## Layers

**Frontend Presentation Layer:**
- Purpose: Render UI and handle user interaction
- Location: `frontend/src/components/`
- Contains: Presentational + container-style components (`CuteHeader.tsx`, `TaskManager.tsx`, `AnalyticsDashboard.tsx`, `AIAssistant.tsx`, `AuthModal.tsx`)
- Depends on: `frontend/src/services/api.ts`, `frontend/src/types.ts`
- Used by: `frontend/src/App.tsx`

**Frontend Service Layer:**
- Purpose: Centralize HTTP calls, JWT injection, and mock fallback data
- Location: `frontend/src/services/api.ts`
- Contains: `AuthService`, `TaskService`, `AnalyticsService`, `RAGService` + module-level `mockTasks`/`mockMemories`
- Depends on: axios, `frontend/src/types.ts`
- Used by: `App.tsx` and all components

**Backend API Layer (routers):**
- Purpose: Expose REST endpoints, validate input, call ORM/service logic
- Location: `backend/routes/`
- Contains: `auth_routes.py`, `task_routes.py`, `analytics_routes.py`, `rag_routes.py`
- Depends on: `backend/models.py`, `backend/schemas.py`, `backend/auth.py`, `backend/database.py`, `backend/rag_service.py`
- Used by: `backend/main.py`

**Backend Core/Service Layer:**
- Purpose: Business logic, persistence, and the RAG pipeline
- Location: `backend/` root modules (`auth.py`, `database.py`, `models.py`, `schemas.py`, `rag_service.py`)
- Depends on: SQLAlchemy, ChromaDB, SentenceTransformers, external LLM APIs
- Used by: `backend/routes/`

**Data Layer:**
- Purpose: Durable state — relational + vector
- Location: SQLite file `backend/cozy_productivity.db` (or `DATABASE_URL`), ChromaDB dir `backend/chroma_db/`
- Managed by: `backend/database.py`, `backend/rag_service.py`

## Data Flow

### Primary Request Path (e.g., task list)

1. `TaskManager.tsx` mounts / `App.tsx` calls `TaskService.getTasks()` (`frontend/src/services/api.ts:136`)
2. axios request interceptor injects `Authorization: Bearer <cozy_token>` from `localStorage` (`frontend/src/services/api.ts:13-19`)
3. Dev server proxies `/api` to `http://localhost:8000` via `frontend/vite.config.ts:9-14`; Docker: nginx serves SPA and proxies `/api`
4. `task_routes.py:14` `get_tasks` runs, guarded by `Depends(auth.get_current_user)` → `auth.py:35` decodes JWT, loads user from DB
5. SQLAlchemy query filters by `current_user.id`, ordered by `created_at desc` (`task_routes.py:20-27`)
6. Result serialized via `schemas.TaskResponse` and returned; on network error the service returns `mockTasks` instead (`api.ts:141`)

### Task CRUD → RAG Memory Flow

1. `create_task`/`update_task`/`complete_task`/`delete_task` in `backend/routes/task_routes.py` commit the ORM change
2. After commit, the route calls `rag_service.format_task_memory(action_type, task_data)` (`rag_service.py:54`) to produce a natural-language sentence (CREATE/COMPLETE/DELAY/UPDATE/OVERDUE)
3. `rag_service.store_memory(user_id, text, action, task_id)` (`rag_service.py:102`) embeds the sentence with `all-MiniLM-L6-v2` and adds it to per-user ChromaDB collection `user_{user_id}_memories` (`rag_service.py:114`); falls back to module-level `in_memory_docs` list if ChromaDB/SentenceTransformers import fails (`rag_service.py:43-50`)
4. Startup seeding in `backend/main.py:34-133` creates a demo user (`demo@cozy.app`), 5 tasks, and 4 extra historical memories

### RAG Query Flow (Multi-Agent Pipeline)

1. `AIAssistant.tsx` sends question + provider to `RAGService.queryAssistant` → `POST /api/rag/query` (`backend/routes/rag_routes.py:12`)
2. `rag_service.run_rag_pipeline()` (`rag_service.py:378`) executes:
   - **Step 1 — Retrieval Agent:** `RetrievalAgent.retrieve(user_id, question, top_k=5)` (`rag_service.py:144`) — semantic search over ChromaDB, relevance = `1.0 - distance`
   - **Step 2 — Evaluator Agent:** `EvaluatorAgent.evaluate(query, memories)` (`rag_service.py:198`) — filters memories with `relevance_score < 0.15`, computes confidence = `avg_score + 0.2` capped at 1.0
   - **Step 3 — Multi-LLM Agent:** `MultiLLMQueryAgent.query(...)` (`rag_service.py:220`) — routes to Ollama (default), OpenAI, Gemini, or Grok via raw `requests.post`; every provider failure falls through to the rule-based `_generate_smart_fallback()` (`rag_service.py:319`)
3. Response assembles `answer`, `retrieved_memories`, `evaluator_score`, agent names, `execution_time_ms` (`rag_service.py:404-412`) and returns as `schemas.RAGQueryResponse`

### Auth Flow

1. `AuthModal.tsx` → `AuthService.login/register` → `POST /api/auth/login` (`auth_routes.py:36`)
2. bcrypt verify via `auth.verify_password` (`auth.py:19`), JWT created with `sub` = email, 7-day expiry (`auth.py:25-33`)
3. Token stored in `localStorage['cozy_token']`; attached to all subsequent requests by the axios interceptor

**State Management:**
- Frontend: local `useState` in `App.tsx` (`user`, `tasks`, `analytics`, `activeTab`); children receive props + `onTaskChange`/`onSuccess` callbacks; `AnalyticsDashboard` and `AIAssistant` fetch their own data
- Backend: stateless; per-request DB session via `get_db` dependency; JWT is the only session mechanism; auth token valid 7 days
- Vector store: per-user ChromaDB collections keyed by `user_{user_id}_memories`

## Key Abstractions

**Service objects (frontend):**
- Purpose: Group related API calls and encapsulate mock fallback per endpoint family
- Examples: `AuthService`, `TaskService`, `AnalyticsService`, `RAGService` — all in `frontend/src/services/api.ts`
- Pattern: Plain exported objects of async methods; each method wrapped in `try/catch` returning mock data on failure

**Agent classes (RAG):**
- Purpose: Represent pipeline stages as isolated units
- Examples: `RetrievalAgent`, `EvaluatorAgent`, `MultiLLMQueryAgent` — all in `backend/rag_service.py`
- Pattern: `@staticmethod`-only classes; no instantiation, no internal state; orchestrated by `run_rag_pipeline()`

**Dependency-injected DB session:**
- Purpose: Provide a request-scoped SQLAlchemy session to route handlers
- Example: `get_db` in `backend/database.py:17`, consumed as `db: Session = Depends(get_db)`
- Pattern: FastAPI generator dependency with `yield`/`finally: db.close()`

**Current-user dependency:**
- Purpose: Resolve the authenticated user from the Bearer token for every protected route
- Example: `get_current_user` in `backend/auth.py:35`, consumed as `current_user: models.User = Depends(auth.get_current_user)`
- Pattern: FastAPI dependency chaining (uses `get_db` internally)

**Props-interface components (frontend):**
- Purpose: Type component contracts
- Example: `interface Props { tasks: Task[]; onTaskChange: () => void; }` in `frontend/src/components/TaskManager.tsx:6-9`
- Pattern: Local `Props` interface per component; named `export const X: React.FC<Props>`

## Entry Points

**Backend:**
- Location: `backend/main.py`
- Invocation: `uvicorn main:app --reload --port 8000` (dev) or `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]` (`backend/Dockerfile`)
- Responsibilities: Create FastAPI app (`title="Cozy AI Productivity & RAG Intelligence System"`, `version="2.0.0"`), register CORS middleware (allow all origins), include 4 routers, `Base.metadata.create_all` on import, seed demo user/tasks/memories on startup, serve `GET /` health/root info

**Frontend:**
- Location: `frontend/src/main.tsx` → `frontend/src/App.tsx`
- Invocation: `npm run dev` (Vite dev server on port 3000) or `docker-compose up --build`
- Responsibilities: Mount React app into `#root`; `App.tsx` owns top-level state and tab routing between `tasks` | `analytics` | `assistant`

## Architectural Constraints

- **Threading:** Backend is single-threaded async-capable FastAPI on uvicorn; SQLite requires `check_same_thread: False` (`backend/database.py:10`). All route handlers are synchronous `def` (FastAPI runs them in a threadpool). RAG HTTP calls to LLM providers are blocking `requests.post` with 5–10s timeouts (`backend/rag_service.py:247, 271, 289, 307`)
- **Global state:** Module-level singletons in `backend/rag_service.py`: `chroma_client`, `embedding_model`, and the in-memory fallback `in_memory_docs` list (process-wide, non-persistent). `cozy_token` in browser `localStorage` (`frontend/src/services/api.ts:14`) is the client-side session store
- **Circular imports:** None detected — `main.py` imports modules/routes; routes import `models`, `schemas`, `auth`, `database`, `rag_service`; `auth.py` imports `models` and `database`; no module imports `main.py`
- **DB access style:** Raw SQLAlchemy Core-style queries (`db.query(Model).filter(...)`) rather than SQLAlchemy 2.0 select() statements; no repository layer; routes contain query logic inline
- **Two-service deployment:** `docker-compose.yml` defines `backend` (port 8000) and `frontend` (port 3000→80); frontend build uses Vite proxy in dev, nginx static serving in Docker; ChromaDB and SQLite persisted via named host volumes (`docker-compose.yml:15-16`)
- **Demo data dependency:** The system seeds `demo@cozy.app` / `cozy123` on startup (`backend/main.py:38-47`), and the frontend falls back to a hard-coded mock user when the API is unreachable — the UI assumes a logged-in-like state even without auth

## Anti-Patterns

### Fallback-to-mock Hides Real Errors

**What happens:** Every method in `frontend/src/services/api.ts` catches ALL exceptions and silently returns mock data (e.g., `api.ts:136-143`, `api.ts:228-251`). A failing backend produces a working-looking UI with fabricated data.
**Why it's wrong:** Production issues are invisible; users get phantom data (fake tasks, fake analytics); a silent mock path after a real auth failure can mask 401s.
**Do this instead:** Gate mock fallback behind an explicit flag (e.g., `VITE_USE_MOCK`) or only on network-level errors (`axios.isAxiosError(e) && !e.response`); surface non-network errors to the user.

### Secret Defaults Committed in Code

**What happens:** `backend/auth.py:12` hard-codes `JWT_SECRET_KEY` default `"cozy_rag_productivity_tracker_super_secret_key_2026"`, and `docker-compose.yml:12` sets the same value as an environment variable.
**Why it's wrong:** Anyone with the repo can forge valid JWTs for any user in any deployment that doesn't override the key.
**Do this instead:** Require `JWT_SECRET_KEY` to be provided via environment in production (fail fast if missing), and remove the default from `docker-compose.yml`.

### Blocking LLM Calls in Request Path

**What happens:** `MultiLLMQueryAgent.query` (`backend/rag_service.py:220`) performs synchronous HTTP calls (up to 10s timeout) inside the `/api/rag/query` request handler.
**Why it's wrong:** A slow or down LLM provider stalls the FastAPI worker thread; multiple concurrent queries degrade the whole API.
**Do this instead:** Run the LLM call in a background task (`BackgroundTasks`) or job queue, and return the answer asynchronously, or shorten timeouts and cache results.

## Error Handling

**Strategy:** Defensive per-call `try/except` with layered fallbacks.

**Patterns:**
- FastAPI `HTTPException` for expected errors: duplicate email → 400 (`auth_routes.py:14-17`), bad credentials → 401 (`auth_routes.py:39-44`), missing task → 404 (`task_routes.py:69, 124, 152`), empty question → 400 (`rag_routes.py:17-18`)
- RAG pipeline degrades gracefully: ChromaDB import failure → in-memory store (`rag_service.py:43-50`); provider connection failure → next provider → rule-based fallback engine (`rag_service.py:253, 316-317`)
- Startup seeding wrapped in try/except with rollback (`backend/main.py:129-131`)
- Frontend: per-service `try/catch` → mock data (see anti-pattern above); console.error used in `AIAssistant.tsx:32`

## Cross-Cutting Concerns

**Logging:** Python `logging` module — `logger = logging.getLogger("rag_service")` (`rag_service.py:32`); `logger.error`/`logger.info` used in `rag_service.py` for ChromaDB and provider failures; startup seeding failures use `print` (`backend/main.py:131`). No structured logging, no log aggregation.

**Validation:** Pydantic v2 schemas in `backend/schemas.py` (`from_attributes = True` for ORM responses); field constraints like `min_length`/`max_length` on names/passwords/titles; enums for priority/status are NOT enforced — plain `str` fields (e.g., `schemas.py:33-34`), so invalid values flow through to DB.

**Authentication:** JWT (HS256) with bcrypt password hashing (`backend/auth.py`); OAuth2PasswordBearer token scheme with `tokenUrl="/api/auth/login"` (`auth.py:17`); every route except auth endpoints and `/` requires `Depends(auth.get_current_user)`; frontend stores token in `localStorage` and attaches via axios interceptor.

---

*Architecture analysis: 2026-08-11*
