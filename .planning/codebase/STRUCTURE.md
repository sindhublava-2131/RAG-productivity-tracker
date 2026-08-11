# Codebase Structure

**Analysis Date:** 2026-08-11

## Directory Layout

```
RAG-productivity-tracker/
├── backend/                        # FastAPI + SQLAlchemy + RAG engine
│   ├── alembic/                    # DB migrations
│   │   ├── env.py                  # Alembic env (reads DATABASE_URL from settings)
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial.py     # Initial users + tasks schema
│   ├── alembic.ini                 # Alembic config
│   ├── core/
│   │   └── config.py               # pydantic-settings Settings object (single source of truth)
│   ├── routes/                     # API router modules (5 routers)
│   │   ├── health_routes.py        # /health/live, /health/ready
│   │   ├── auth_routes.py          # register / login / me
│   │   ├── task_routes.py          # tasks CRUD + complete
│   │   ├── analytics_routes.py     # 11 metrics
│   │   └── rag_routes.py           # /api/rag/query, /api/rag/memories
│   ├── services/
│   │   └── rag/                    # RAG subsystem package
│   │       ├── service.py          # RagService composition root + singleton
│   │       ├── pipeline.py         # retrieval → rerank → context → generate → validate
│   │       ├── retrieval.py        # HybridRetriever (semantic + lexical)
│   │       ├── reranking.py        # Reranker (4-factor deterministic scoring)
│   │       ├── grounding.py        # GroundingValidator (citation check)
│   │       ├── context.py          # ContextBuilder / SourceBlock
│   │       ├── embeddings.py       # EmbeddingService (+ fallback, Fake for tests)
│   │       ├── memory.py           # MemoryRecord, MemoryIngestionService, format_task_memory
│   │       ├── vector_store.py     # VectorStore ABC, ChromaVectorStore, InMemoryVectorStore
│   │       └── providers/          # LLM providers
│   │           ├── base.py         # LLMProvider ABC, ProviderResult, LLMError, fakes
│   │           ├── registry.py     # get_provider() factory
│   │           ├── ollama.py / openai.py / gemini.py / grok.py
│   │           └── _http.py        # shared async post_json (timeout/retry)
│   ├── tests/                      # pytest suite (offline, deterministic)
│   │   ├── conftest.py             # fixtures: client, db_session, fakes, auth headers
│   │   ├── fixtures/rag/
│   │   │   └── evaluation_dataset.py  # RAG benchmark dataset
│   │   ├── test_auth.py  test_tasks.py  test_analytics.py
│   │   ├── test_health.py  test_rag.py  test_security.py
│   │   └── __init__.py
│   ├── main.py                     # App factory, lifespan, CORS, middleware, router registration
│   ├── database.py                 # Engine, session, Base, get_db, _utcnow
│   ├── models.py                   # User, Task ORM models (2-table schema)
│   ├── schemas.py                  # Pydantic request/response schemas + enums
│   ├── auth.py                     # JWT + bcrypt helpers, get_current_user
│   ├── pyproject.toml              # Project metadata, deps, ruff/mypy/pytest config
│   ├── requirements.txt            # `-e .` (editable install from pyproject.toml)
│   └── Dockerfile                  # python:3.11-slim; alembic upgrade head && uvicorn
├── frontend/                       # React 18 + Vite + Tailwind SPA
│   ├── src/
│   │   ├── components/             # UI components
│   │   │   ├── CuteHeader.tsx
│   │   │   ├── AuthModal.tsx
│   │   │   ├── TaskManager.tsx
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   ├── AIAssistant.tsx
│   │   │   └── AIAssistant.test.tsx
│   │   ├── services/
│   │   │   ├── api.ts              # axios client + interceptors + 4 service objects
│   │   │   └── api.test.ts
│   │   ├── test/
│   │   │   └── setup.ts            # vitest setup (jest-dom, cleanup, localStorage reset)
│   │   ├── App.tsx                 # Root component, tab state, data orchestration
│   │   ├── main.tsx                # React entry point
│   │   ├── types.ts                # Shared TS interfaces
│   │   └── index.css               # Tailwind entry + custom cozy styles
│   ├── index.html                  # HTML shell (Google Fonts, root div)
│   ├── package.json / package-lock.json
│   ├── vite.config.ts              # Port 3000, /api proxy, vitest test block
│   ├── tailwind.config.js          # "cozy" palette, shadows, fonts
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── .eslintrc.cjs               # ESLint 8 + typescript-eslint
│   ├── nginx.conf                  # SPA serving + /api reverse proxy
│   └── Dockerfile                  # node:20 build → nginx:alpine
├── .github/
│   └── workflows/
│       └── ci.yml                  # backend-ci, frontend-ci, docker-smoke-test
├── .planning/                      # GSD workflow artifacts
│   └── codebase/                   # This codebase map (7 docs)
├── docker-compose.yml              # db (PostgreSQL 16) + backend (8000) + frontend (3000)
├── setup.py                        # One-command environment setup (venv, deps, migrations, npm)
├── start.py                        # One-command launcher (backend + frontend + browser)
├── .gitignore
└── README.md
```

Runtime-generated artifacts (gitignored): `backend/cozy_productivity.db` (SQLite), `backend/chroma_db/` (vector store), `frontend/dist/` (build output), `backend/venv/`, `frontend/node_modules/`.

## Directory Purposes

**`backend/`**
- Purpose: All server-side code — FastAPI app, ORM, schemas, auth, migrations, RAG engine
- Contains: root core modules, `core/`, `routes/`, `services/rag/`, `tests/`, `alembic/`
- Key files: `main.py` (composition root), `core/config.py` (settings), `services/rag/service.py` (RAG root)

**`backend/core/`**
- Purpose: Cross-cutting configuration
- Contains: `config.py` — the single `Settings` object read by every other module

**`backend/routes/`**
- Purpose: HTTP endpoint handlers, one router per domain
- Contains: `health_routes.py`, `auth_routes.py`, `task_routes.py`, `analytics_routes.py`, `rag_routes.py`
- Convention: Each file defines `router = APIRouter(prefix="/api/<domain>", tags=[...])` and is registered in `backend/main.py`

**`backend/services/rag/`**
- Purpose: The grounded RAG memory subsystem, decomposed into single-responsibility modules
- Contains: `service.py` (composition root), `pipeline.py` (orchestration), `retrieval.py`, `reranking.py`, `grounding.py`, `context.py`, `embeddings.py`, `memory.py`, `vector_store.py`, `providers/`
- Convention: modules depend on abstractions (`VectorStore`, `EmbeddingService`, `LLMProvider`); fakes live alongside real implementations for offline testing

**`backend/tests/`**
- Purpose: Offline, deterministic pytest suite (in-memory SQLite + fake RAG components)
- Contains: `conftest.py` (fixtures), per-domain `test_*.py`, `fixtures/rag/evaluation_dataset.py`
- Convention: `test_<domain>.py` naming; API tests use the `client` fixture; pure logic tests use fakes directly

**`frontend/src/`**
- Purpose: All application source (components, services, types, entry)
- Contains: `components/`, `services/`, `test/`, `App.tsx`, `main.tsx`, `types.ts`, `index.css`

**`frontend/src/components/`**
- Purpose: UI building blocks, one file per component, named exports
- Contains: `CuteHeader.tsx`, `AuthModal.tsx`, `TaskManager.tsx`, `AnalyticsDashboard.tsx`, `AIAssistant.tsx` (+ co-located `AIAssistant.test.tsx`)
- Convention: local `interface Props` + `export const X: React.FC<Props>`

**`frontend/src/services/`**
- Purpose: API access layer
- Contains: `api.ts` with axios instance, interceptors, `ApiError`, `setUnauthorizedHandler`, and `AuthService` / `TaskService` / `AnalyticsService` / `RAGService`; `api.test.ts` co-located

**`.github/workflows/`**
- Purpose: CI/CD automation
- Contains: `ci.yml` — backend lint/typecheck/test, frontend lint/typecheck/test/build, Docker compose smoke test

**`.planning/`**
- Purpose: GSD workflow artifacts (plans, codebase maps, specs)
- Contains: `codebase/` (this analysis output)
- Committed: Yes (planning state tracked in git)

## Key File Locations

**Entry Points:**
- `backend/main.py`: FastAPI app creation, lifespan, router registration, `GET /` root
- `frontend/src/main.tsx`: React DOM mount into `#root`
- `frontend/src/App.tsx`: Root component — tab switching, auth state, task/analytics data load
- `setup.py` / `start.py` (repo root): one-command dev environment setup and system launcher

**Configuration:**
- `backend/core/config.py`: All env-driven settings (pydantic-settings)
- `backend/pyproject.toml`: Python dependencies + ruff/mypy/pytest config
- `backend/alembic.ini` + `backend/alembic/env.py`: Migration wiring
- `frontend/vite.config.ts`: Dev port 3000, `/api` proxy → `localhost:8000`, vitest config
- `frontend/tailwind.config.js`: Custom `cozy` color palette, radii, shadows, font stack
- `frontend/tsconfig.json`: `strict: true`, bundler moduleResolution, `jsx: react-jsx`
- `frontend/.eslintrc.cjs`: ESLint rules
- `frontend/nginx.conf`: Production SPA serving + `/api` proxy → `backend:8000`
- `docker-compose.yml`: Three services (`db`, `backend`, `frontend`), named volumes, healthchecks
- `.gitignore`: Excludes `node_modules/`, `backend/venv/`, `*.db`, `backend/chroma_db/`, `frontend/dist/`, `.env`, caches

**Core Logic:**
- `backend/models.py`: `User` and `Task` SQLAlchemy models (strict 2-table schema)
- `backend/schemas.py`: Pydantic v2 schemas — `UserCreate/Login/Response/Token`, `TaskBase/Create/Update/Response`, `AnalyticsResponse`, `RAGQueryRequest/Response`, `MemoryRecord/MemoryListResponse`, `HealthResponse/ReadinessResponse`, enums `Priority`/`Status`/`TaskAction`
- `backend/auth.py`: bcrypt hashing, JWT encode/decode, `get_current_user` FastAPI dependency
- `backend/services/rag/pipeline.py`: The 5-stage grounded RAG pipeline
- `backend/services/rag/memory.py`: `format_task_memory()` (single source of memory phrasing) + `MemoryIngestionService`
- `backend/services/rag/vector_store.py`: ChromaDB adapter + in-memory fake
- `frontend/src/services/api.ts`: axios instance + interceptors + service objects

**Testing:**
- `backend/tests/`: pytest suite — auth, tasks, analytics, health, RAG pipeline + benchmark, security regressions
- `frontend/src/services/api.test.ts`, `frontend/src/components/AIAssistant.test.tsx`: vitest suite
- `backend/tests/fixtures/rag/evaluation_dataset.py`: 8-case RAG retrieval benchmark (exact/semantic/recency/irrelevant/multi/empty/ambiguous)

## Naming Conventions

**Files:**
- Backend: snake_case for modules (`task_routes.py`, `vector_store.py`); `_routes.py` suffix for router modules; `_service.py` for service modules
- Frontend: PascalCase for components (`TaskManager.tsx`, `AnalyticsDashboard.tsx`); `api.ts`, `types.ts` lowercase for infrastructure; `*.test.ts(x)` co-located with the unit under test

**Directories:**
- Backend: `routes/` (plural) for API router modules, `services/` for service packages, `core/` for config
- Frontend: `components/`, `services/`, `test/` (plural/lowercase)

**Functions:**
- Backend: snake_case (`get_password_hash`, `create_access_token`, `store_memory_from_task`, `format_task_memory`); route handlers are descriptive verbs (`get_tasks`, `create_task`, `update_task`, `complete_task`, `login_user`, `register_user`, `query_rag_assistant`)
- Frontend: camelCase for service methods and handlers (`getTasks`, `handleSave`, `handleComplete`, `fetchAnalytics`, `reloadData`)

**Variables:**
- Backend: snake_case (`password_hash`, `access_token`, `current_user`, `task_in`)
- Frontend: camelCase (`activeTab`, `editingTask`, `isModalOpen`); state setters follow `const [x, setX] = useState(...)`

**Types:**
- Backend: Pydantic schemas use domain-suffixed PascalCase (`UserCreate`, `TaskResponse`, `RAGQueryRequest`); enums in PascalCase (`Priority`, `Status`, `TaskAction`)
- Frontend: PascalCase interfaces in `frontend/src/types.ts` (`User`, `Task`, `AnalyticsData`, `RAGResponse`, `MemoryRecord`); string-literal union aliases `PriorityType`, `StatusType`

**Classes:**
- Python: PascalCase, role-suffixed (`HybridRetriever`, `Reranker`, `GroundingValidator`, `ContextBuilder`, `EmbeddingService`, `MemoryIngestionService`, `ChromaVectorStore`, `RagPipeline`, `RagService`)

## Where to Add New Code

**New Feature:**
- New frontend view: add component in `frontend/src/components/`, register tab in `frontend/src/App.tsx`, add API methods to the relevant service object in `frontend/src/services/api.ts`, add types to `frontend/src/types.ts`, co-locate a `*.test.tsx`
- New backend endpoint: add router file `backend/routes/<name>_routes.py` following the `APIRouter(prefix="/api/<name>")` pattern, register in `backend/main.py`, add schemas to `backend/schemas.py`, add a `test_<name>.py` in `backend/tests/`
- New backend domain logic: add a module under `backend/services/<domain>/` (mirroring the `services/rag/` package layout), import it from the router
- New RAG behavior: extend the relevant module in `backend/services/rag/` (`retrieval.py`, `reranking.py`, `grounding.py`, `context.py`, `pipeline.py`) rather than adding inline logic to routes

**New Component/Module:**
- Implementation: `frontend/src/components/<Name>.tsx` — one file per component, named export, local `Props` interface; or `backend/routes/<name>_routes.py` for API modules

**Utilities:**
- Frontend shared helpers: `frontend/src/services/` (or a new `frontend/src/utils/` directory following the service-module convention)
- Backend helpers: `backend/core/` for cross-cutting config; domain helpers live in their service package

**Tests:**
- Backend: add `backend/tests/test_<domain>.py` using the shared `conftest.py` fixtures (`client`, `auth_headers`, `db_session`, `rag_service`, fakes)
- Frontend: co-locate `*.test.tsx` beside the component/service and rely on the vitest config in `frontend/vite.config.ts`

## Special Directories

**`backend/chroma_db/`**
- Purpose: Persistent ChromaDB vector store created at runtime by `chromadb.PersistentClient` (`backend/services/rag/vector_store.py`)
- Generated: Yes (runtime)
- Committed: No (gitignored); mounted as named volume `chroma_data` in Docker

**`backend/venv/`**
- Purpose: Python virtual environment for local development
- Generated: Yes
- Committed: No (gitignored)

**`frontend/dist/`**
- Purpose: Production build output (`npm run build`)
- Generated: Yes
- Committed: No (gitignored)

**`.planning/`**
- Purpose: GSD workflow state — plans, codebase maps, milestone artifacts
- Generated: No (hand-authored)
- Committed: Yes

---

*Structure analysis: 2026-08-11*
