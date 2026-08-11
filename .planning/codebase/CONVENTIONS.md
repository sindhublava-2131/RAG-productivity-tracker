# Coding Conventions

**Analysis Date:** 2026-08-11

## Naming Patterns

**Files:**
- **Python modules:** `snake_case.py`, one domain per file — `backend/models.py`, `backend/schemas.py`, `backend/auth.py`, `backend/database.py`, `backend/core/config.py`. Route modules live in `backend/routes/` with a `_routes` suffix: `health_routes.py`, `auth_routes.py`, `task_routes.py`, `analytics_routes.py`, `rag_routes.py`. RAG package modules use single-purpose names in `backend/services/rag/`: `retrieval.py`, `reranking.py`, `grounding.py`, `context.py`, `embeddings.py`, `memory.py`, `vector_store.py`, `pipeline.py`, `service.py`.
- **React components:** PascalCase `*.tsx`, one component per file — `frontend/src/components/CuteHeader.tsx`, `TaskManager.tsx`, `AuthModal.tsx`, `AnalyticsDashboard.tsx`, `AIAssistant.tsx`.
- **Service layer:** lowercase `api.ts` under `frontend/src/services/api.ts`.
- **Shared types:** `frontend/src/types.ts`.
- **Tests:** `test_<domain>.py` in `backend/tests/`; `*.test.ts(x)` co-located with the unit in the frontend.

**Functions:**
- **Python:** `snake_case` (`get_password_hash`, `create_access_token`, `store_memory_from_task`, `format_task_memory` in `backend/auth.py` and `backend/services/rag/memory.py`). Route handlers are descriptive verbs in `backend/routes/*.py`: `get_tasks`, `create_task`, `update_task`, `complete_task`, `delete_task`, `login_user`, `register_user`, `query_rag_assistant`.
- **TypeScript:** `camelCase` for hooks and handlers (`fetchAnalytics`, `handleSave`, `handleComplete`, `openCreateModal` in `frontend/src/components/TaskManager.tsx`; `reloadData`, `handleLogout` in `frontend/src/App.tsx`).

**Variables:**
- **Python:** `snake_case` (`db`, `current_user`, `task_in`, `status_filter` in `backend/routes/task_routes.py`); private helpers prefixed `_` (`_utcnow`, `_persist_memory`, `_aware`, `_parse_iso`).
- **TypeScript:** `camelCase` (`filterStatus`, `editingTask`, `isModalOpen` in `frontend/src/components/TaskManager.tsx`). Boolean state uses `is*` prefix (`isOpen`, `isLogin`, `isAuthOpen`). State setters follow `const [x, setX] = useState(...)`.

**Types:**
- **Python:** Pydantic schemas in `backend/schemas.py` use base/suffix naming: `TaskBase` → `TaskCreate`/`TaskUpdate`/`TaskResponse`; auth has `UserCreate`, `UserLogin`, `UserResponse`, `Token`; enums `Priority`, `Status`, `TaskAction`.
- **TypeScript:** `interface` names are plain domain nouns (`User`, `Task`, `AnalyticsData`, `MemoryRecord`, `RAGResponse`) in `frontend/src/types.ts`; string-literal union types use `Type` suffix (`PriorityType`, `StatusType`). Component props use a local `interface Props` per file (see `frontend/src/components/TaskManager.tsx`, `CuteHeader.tsx`, `AuthModal.tsx`).

## Code Style

**Formatting:**
- **Python:** 4-space indentation, 110-char line length (set in `[tool.ruff] line-length = 110`), `from __future__ import annotations` at the top of every module, standard-library imports first then third-party then local. Ruff config in `backend/pyproject.toml` (`select = ["E", "F", "W", "I", "UP", "B", "ASYNC"]`, `ignore = ["E501"]`).
- **TypeScript:** semicolons required and always present (`frontend/src/App.tsx`, all components, `frontend/src/services/api.ts`). Single quotes everywhere in TS/TSX (`import { User } from '../types';`). No Prettier config exists.

**Linting:**
- Backend: `ruff check .` (CI + setup.py install `ruff`); typecheck `mypy --config-file pyproject.toml` (pydantic plugin, strict-ish with `ignore_missing_imports = true`).
- Frontend: `npm run lint` (ESLint 8 + typescript-eslint + react-hooks + react-refresh via `frontend/.eslintrc.cjs`; `--max-warnings 0`).

**TypeScript strictness:**
- `frontend/tsconfig.json` sets `"strict": true` and `"noFallthroughCasesInSwitch": true`; `noUnusedLocals`/`noUnusedParameters` are `false` (so the `_completedToday` unused-prop pattern in `CuteHeader.tsx` compiles). Keep `strict` on; avoid `any` where a type is available (`no-explicit-any` is a warn-level ESLint rule).

## Import Organization

**Python (`backend/routes/*.py`, `backend/services/rag/*.py`):**
1. Standard library (`from __future__ import annotations`, `logging`, `datetime`)
2. Third-party (`from fastapi import APIRouter, Depends, HTTPException, status`, `from sqlalchemy.orm import Session`, `import httpx`)
3. Local modules — absolute, non-relative: `import models`, `import schemas`, `import auth`, `from database import get_db`, `from services.rag.service import get_rag_service`

Example from `backend/routes/rag_routes.py`:
```python
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db
from services.rag.service import get_rag_service
```

**TypeScript (`frontend/src/**`):**
1. React/third-party (`import React, { useState } from 'react';`, `import axios from 'axios';`, lucide icons: `import { Plus, Check, Clock } from 'lucide-react';`)
2. Local relative imports, `../` style: `import { User, Task } from '../types';`, `import { TaskService } from '../services/api';`

**Path Aliases:**
- None. Frontend uses relative imports only. Vite proxy maps `/api` → `http://localhost:8000` in `frontend/vite.config.ts`; the frontend never references the backend URL directly (`const API_BASE = '/api'` in `frontend/src/services/api.ts`).

## Error Handling

**Backend — typed, layered:**
- `HTTPException` for expected API failures: duplicate email → 400 (`backend/routes/auth_routes.py`), bad credentials → 401 with `WWW-Authenticate` header, missing task → 404 with `detail="Task not found"` (`backend/routes/task_routes.py`), empty question → 400 (`backend/routes/rag_routes.py`). Use `status.HTTP_*` constants (`status.HTTP_404_NOT_FOUND`).
- `MemoryIngestionError` (subclass of `RuntimeError`) for vector-store persistence failures (`backend/services/rag/memory.py`) — routes catch and log it (best-effort, see ARCHITECTURE anti-patterns).
- `LLMError` (subclass of `RuntimeError`) for provider call failures; shared `post_json` in `backend/services/rag/providers/_http.py` retries with backoff then raises; the pipeline converts failures into a graceful "currently unavailable" answer with `confidence=0`, `grounded=False`.
- Authentication dependency `auth.get_current_user` (`backend/auth.py`) raises 401 itself — routes never re-check auth.

**Frontend — typed `ApiError` propagation (no mock fallback):**
- `frontend/src/services/api.ts` defines `ApiError extends Error` with `status` and `detail`; every service method catches axios/network errors and rethrows `toApiError(e)`. The old mock-fallback engine has been removed — errors are visible to the UI.
- `extractDetail()` handles FastAPI `detail` strings or arrays, network errors ("Network error — cannot reach the server..."), and unknown errors.
- Components display `error.message`: `AuthModal.tsx` shows it inline; `AIAssistant.tsx` shows an error card; `App.tsx` catches load failures and resets state to empty rather than crashing.
- The axios response interceptor handles 401 globally: clears `localStorage`, calls `setUnauthorizedHandler` (wired in `App.tsx` to log out and reopen the auth modal).

## Logging

**Framework:** stdlib `logging` configured once in `backend/main.py` (`level=settings.LOG_LEVEL`, format `%(asctime)s %(levelname)s [%(name)s] %(message)s`); frontend uses `console.error` only.

**Patterns:**
- Named loggers per module: `logger = logging.getLogger("cozy.main")`, `"cozy.auth"`, `"cozy.routes.tasks"`, `"cozy.rag.service"`, `"cozy.rag.pipeline"`, `"cozy.rag.embeddings"`, `"cozy.rag.providers"`.
- Request-context middleware in `backend/main.py` logs `request_id method path status latency_ms` for every request and returns `X-Request-Id`.
- Key events logged: RAG query summary (`user_id`, retrieval/rerank counts, grounded, latency, provider, model, error_type), memory persistence failures (`MemoryIngestionError`), provider retries/fallbacks, embedding model load.
- No structured logging / log aggregation.

## Comments

**When to Comment:**
- Python: module docstrings on every `services/rag/` module and on `core/config.py`; short docstrings on classes (`HybridRetriever`, `Reranker`, `GroundingValidator`, `RagService`, `MemoryIngestionService`) and key functions (`_utcnow`, `format_task_memory`, `_persist_memory`); section divider comments with `# ---` (`backend/schemas.py`: `# --- Auth Schemas ---`, `# --- Task Schemas ---`).
- Purpose comments before non-obvious logic, e.g. `# SQLite strips tzinfo from DateTime(timezone=True); re-attach UTC` in `backend/routes/analytics_routes.py`.
- Frontend JSX: `{/* Section name */}` comments inside `frontend/src/components/*.tsx` (`{/* Filter & Search Bar */}`, `{/* Task Cards Grid */}` in `TaskManager.tsx`).

**JSDoc/TSDoc:**
- Not used in the frontend. Python uses docstrings on non-trivial modules/classes; route handlers and small helpers generally have none.

## Function Design

**Size:** Route handlers are compact and single-purpose. `backend/routes/analytics_routes.py` `get_analytics` is a ~80-line monolith computing 11 metrics inline with helper `_aware` — a candidate for extraction, but intentionally self-contained. RAG pipeline stages are split across modules (`retrieval.py`, `reranking.py`, `grounding.py`, `context.py`) — keep new logic in the matching module rather than growing `pipeline.py`.

**Parameters:** FastAPI route handlers use `Depends()` for db session and current user: `db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)`. RAG service calls use keyword-only style: `rag.store_memory_from_task(user_id=..., task_id=..., action=..., content=...)`.

**Return Values:**
- Pydantic response models declared on the decorator (`@router.get("", response_model=list[schemas.TaskResponse])`); handlers return ORM objects, Pydantic serializes them (`from_attributes=True`).
- `store_memory_from_task` returns the memory id string; `list_memories` returns `(records, total)`; pipeline `run()` returns a dict matching `RAGQueryResponse`.
- Frontend service methods return `Promise<T>` with explicit annotations (`async getTasks(): Promise<Task[]>`).

## Module Design

**Exports:**
- Backend: `router = APIRouter(prefix="/api/<area>", tags=["..."])` is the single export of every route module, registered in `backend/main.py` via `app.include_router(x_routes.router)`. RAG modules export their classes + `get_rag_service()`/`configure_rag_service()`/`reset_rag_service()` (`backend/services/rag/service.py`). `settings` is the single export of `backend/core/config.py`.
- Frontend: components use **named exports** (`export const TaskManager: React.FC<Props> = ...`). `frontend/src/App.tsx` has both named (`export const App`) and default exports. Services export const objects (`AuthService`, `TaskService`, `AnalyticsService`, `RAGService`) plus `api`, `ApiError`, `setUnauthorizedHandler`. Types export `interface`/`type` declarations from `frontend/src/types.ts`.

**Barrel Files:** `__init__.py` files in `backend/routes/`, `backend/services/rag/`, and `backend/tests/` are empty — imports are always explicit from module paths.

## React-Specific Conventions

- Function components typed `React.FC<Props>`; props defined as local `interface Props` and destructured in the signature (`frontend/src/components/CuteHeader.tsx`).
- Hooks: `useState` + `useEffect` only; no custom hooks, no context, no router (tab switching via `useState<'tasks' | 'analytics' | 'assistant'>` in `frontend/src/App.tsx`).
- `useEffect(() => { fetchX(); }, [])` mount-and-fetch pattern in `App.tsx`, `AnalyticsDashboard.tsx`, `AIAssistant.tsx`.
- Tailwind utility classes with arbitrary hex values (`bg-[#FFDFE5]`) everywhere; `frontend/tailwind.config.js` also defines semantic tokens (`cozy.rose`, `cozy.lavender`, `shadow-cozy`, `rounded-4xl`). Both are used — prefer theme tokens for new code, arbitrary values are accepted.
- `className` conditionals use template literals with ternaries (`TaskManager.tsx`, `CuteHeader.tsx`).
- Emojis in UI copy are a deliberate aesthetic convention (`🌸`, `🐱`, `🤖`) — keep for consistency.
- Error/empty states are cute and friendly ("No tasks found! 🐱💤"), matching the cozy brand.

## Security / Credential Conventions

- `JWT_SECRET_KEY` has **no default**: production fails fast (`backend/core/config.py` validator); development generates an ephemeral per-process secret via `secrets.token_urlsafe(48)`. **Do not reintroduce a hardcoded default.**
- Passwords hashed with bcrypt directly (`backend/auth.py`) — no passlib.
- LLM API keys read from settings/env only (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`); Gemini key sent via `x-goog-api-key` header, never a URL query param.
- Demo seeding gated by `SEED_DEMO` and only honored when `APP_ENV != production` (`backend/main.py`).
- Frontend stores the JWT in `localStorage` under `cozy_token` and injects via axios request interceptor — the single auth wiring point; 401 clears it automatically.
- No `.env` file is committed; `.env` is gitignored.

---

*Convention analysis: 2026-08-11*
