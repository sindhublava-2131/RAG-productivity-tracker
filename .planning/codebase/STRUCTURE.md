# Codebase Structure

**Analysis Date:** 2026-08-11

## Directory Layout

```
RAG-productivity-tracker/
├── backend/                    # FastAPI + SQLAlchemy + RAG engine
│   ├── routes/                 # API router modules (4 routers)
│   │   ├── auth_routes.py
│   │   ├── task_routes.py
│   │   ├── analytics_routes.py
│   │   └── rag_routes.py
│   ├── main.py                 # App factory, CORS, router registration, seeding
│   ├── database.py             # Engine, session, Base, get_db
│   ├── models.py               # User, Task ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── auth.py                 # JWT + bcrypt helpers, get_current_user
│   ├── rag_service.py          # RAG pipeline (agents, memory store, LLM clients)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React 18 + Vite + Tailwind SPA
│   ├── src/
│   │   ├── components/         # UI components
│   │   │   ├── CuteHeader.tsx
│   │   │   ├── AuthModal.tsx
│   │   │   ├── TaskManager.tsx
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   └── AIAssistant.tsx
│   │   ├── services/
│   │   │   └── api.ts          # axios client + 4 service objects + mock data
│   │   ├── App.tsx             # Root component, tab state, data orchestration
│   │   ├── main.tsx            # React entry point
│   │   ├── types.ts            # Shared TS interfaces
│   │   └── index.css           # Tailwind entry + custom CSS
│   ├── index.html              # HTML shell (Google Fonts, root div)
│   ├── package.json
│   ├── vite.config.ts          # Port 3000, /api proxy → localhost:8000
│   ├── tailwind.config.js      # "cozy" palette, shadows, fonts
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml          # backend (8000) + frontend (3000) orchestration
├── .gitignore
└── README.md
```

Runtime-generated artifacts (gitignored): `backend/cozy_productivity.db` (SQLite), `backend/chroma_db/` (vector store), `frontend/dist/` (build output).

## Directory Purposes

**`backend/`**
- Purpose: All server-side code — FastAPI app, ORM, schemas, auth, RAG engine
- Contains: Root-level core modules plus one `routes/` subdirectory
- Key files: `main.py` (composition root), `rag_service.py` (RAG pipeline), `database.py` (DB wiring)

**`backend/routes/`**
- Purpose: HTTP endpoint handlers, one router per domain
- Contains: `auth_routes.py`, `task_routes.py`, `analytics_routes.py`, `rag_routes.py`
- Convention: Each file defines `router = APIRouter(prefix="/api/<domain>", tags=[...])` and is registered in `backend/main.py:29-32`

**`frontend/src/`**
- Purpose: All application source (components, services, types, entry)
- Contains: `components/`, `services/`, `App.tsx`, `main.tsx`, `types.ts`, `index.css`

**`frontend/src/components/`**
- Purpose: UI building blocks, one file per component, named exports
- Contains: 5 components sized 116–375 lines (`TaskManager.tsx` 375, `AIAssistant.tsx` 237, `AnalyticsDashboard.tsx` 222, `AuthModal.tsx` 148, `CuteHeader.tsx` 116)
- Convention: Local `interface Props` + `export const X: React.FC<Props>`

**`frontend/src/services/`**
- Purpose: API access layer
- Contains: single file `api.ts` with `AuthService`, `TaskService`, `AnalyticsService`, `RAGService` and module-level `mockTasks`/`mockMemories` fallbacks

**`.planning/`**
- Purpose: GSD workflow artifacts (plans, codebase maps, specs)
- Contains: `codebase/` (this analysis output), plus per-milestone planning dirs
- Committed: Yes (planning state tracked in git)

## Key File Locations

**Entry Points:**
- `backend/main.py`: FastAPI app creation, router registration, startup seeding, `GET /` root
- `frontend/src/main.tsx`: React DOM mount into `#root`
- `frontend/src/App.tsx`: Root component — tab switching, auth state, task/analytics data load

**Configuration:**
- `backend/requirements.txt`: Python dependencies (FastAPI, SQLAlchemy, chromadb, sentence-transformers, pytest, etc.)
- `backend/Dockerfile`: Python 3.11-slim, uvicorn on port 8000
- `frontend/vite.config.ts`: Dev port 3000, `/api` proxy → `http://localhost:8000`
- `frontend/tailwind.config.js`: Custom `cozy` color palette, border radii, shadows, font stack
- `frontend/tsconfig.json`: `strict: true`, bundler moduleResolution, `jsx: react-jsx`
- `docker-compose.yml`: Two services (`backend`, `frontend`), volume mounts for SQLite + ChromaDB, `host.docker.internal` for Ollama
- `.gitignore`: Excludes `node_modules/`, `backend/venv/`, `*.db`, `backend/chroma_db/`, `frontend/dist/`, `.env`

**Core Logic:**
- `backend/models.py`: `User` and `Task` SQLAlchemy models (strict 2-table schema)
- `backend/schemas.py`: Pydantic v2 schemas — `UserCreate/Login/Response/Token`, `TaskBase/Create/Update/Response`, `AnalyticsResponse`, `RAGQueryRequest/Response`, `MemoryItem`
- `backend/auth.py`: bcrypt hashing, JWT encode/decode, `get_current_user` FastAPI dependency
- `backend/rag_service.py`: `format_task_memory()`, `store_memory()`, `RetrievalAgent`, `EvaluatorAgent`, `MultiLLMQueryAgent`, `run_rag_pipeline()` — the full RAG engine
- `frontend/src/services/api.ts`: axios instance + request interceptor (JWT) + 4 service objects + mock data engine

**Testing:**
- No test files detected anywhere in the repo. `pytest>=7.4.0` is declared in `backend/requirements.txt` but no `tests/` directory or `*_test.py`/`test_*.py` files exist. No frontend test framework is declared.

## Naming Conventions

**Files:**
- Backend: snake_case for modules (`task_routes.py`, `rag_service.py`), `_routes.py` suffix for router modules, `_service.py` suffix for service modules
- Frontend: PascalCase for components (`TaskManager.tsx`, `AnalyticsDashboard.tsx`); `api.ts`, `types.ts` lowercase for infrastructure

**Directories:**
- Backend: `routes/` plural for API router modules
- Frontend: `components/` and `services/` plural

**Functions:**
- Backend: snake_case (`get_password_hash`, `store_memory`, `run_rag_pipeline`); route handlers named for their action (`create_task`, `get_analytics`, `login_user`)
- Frontend: camelCase for service methods and handlers (`getTasks`, `handleSave`, `reloadData`)

**Variables:**
- Backend: snake_case (`password_hash`, `access_token`, `current_user`)
- Frontend: camelCase (`activeTab`, `mockTasks`, `setIsAuthOpen`)

**Types:**
- Backend: Pydantic schemas use PascalCase with domain suffixes (`UserCreate`, `TaskResponse`, `RAGQueryRequest`)
- Frontend: PascalCase interfaces in `frontend/src/types.ts` (`User`, `Task`, `AnalyticsData`, `MemoryItem`, `RAGResponse`); type-union aliases `PriorityType`, `StatusType`

**Classes:**
- Python agent classes: PascalCase with `Agent` suffix (`RetrievalAgent`, `EvaluatorAgent`, `MultiLLMQueryAgent`) in `backend/rag_service.py`

## Where to Add New Code

**New Feature:**
- New frontend view: add component in `frontend/src/components/`, register tab in `frontend/src/App.tsx`, add API methods to the relevant service object in `frontend/src/services/api.ts`, add types to `frontend/src/types.ts`
- New backend endpoint: add router file `backend/routes/<name>_routes.py` following the `APIRouter(prefix="/api/<name>")` pattern, register in `backend/main.py`, add schemas to `backend/schemas.py`
- New backend domain logic: add a module in `backend/` (e.g., `backend/<domain>_service.py`) mirroring `rag_service.py`, import it from the router

**New Component/Module:**
- Implementation: `frontend/src/components/<Name>.tsx` — one file per component, named export, local `Props` interface; or `backend/routes/<name>_routes.py` for API modules

**Utilities:**
- Frontend shared helpers: `frontend/src/services/` (or a new `frontend/src/utils/` directory following the service-module convention)
- Backend helpers: root of `backend/` (e.g., `backend/auth.py` is the existing helper precedent)

**Tests:**
- Not currently established. If adding: create `backend/tests/` for pytest (dependency already declared) and mirror the co-located or `tests/` pattern that the project adopts.

## Special Directories

**`backend/chroma_db/`**
- Purpose: Persistent ChromaDB vector store created at runtime by `chromadb.PersistentClient(path="./chroma_db")` (`backend/rag_service.py:41`)
- Generated: Yes (runtime)
- Committed: No (gitignored)

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
