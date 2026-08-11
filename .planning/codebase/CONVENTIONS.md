# Coding Conventions

**Analysis Date:** 2026-08-11

## Naming Patterns

**Files:**
- **Python modules:** `snake_case.py`, one domain per file — `backend/models.py`, `backend/schemas.py`, `backend/auth.py`, `backend/rag_service.py`, `backend/database.py`. Route modules live in `backend/routes/` with a `_routes` suffix: `backend/routes/auth_routes.py`, `backend/routes/task_routes.py`, `backend/routes/analytics_routes.py`, `backend/routes/rag_routes.py`.
- **React components:** PascalCase `*.tsx`, one component per file — `frontend/src/components/CuteHeader.tsx`, `frontend/src/components/TaskManager.tsx`, `frontend/src/components/AuthModal.tsx`, `frontend/src/components/AnalyticsDashboard.tsx`, `frontend/src/components/AIAssistant.tsx`.
- **Service layer:** lowercase `api.ts` under `frontend/src/services/api.ts`.
- **Shared types:** `frontend/src/types.ts` (singular filename, not `types.ts`).

**Functions:**
- **Python:** `snake_case` (`get_password_hash`, `create_access_token`, `store_memory`, `run_rag_pipeline` in `backend/auth.py` and `backend/rag_service.py`). Route handler names are descriptive verbs in `backend/routes/*.py`: `get_tasks`, `create_task`, `update_task`, `complete_task`, `delete_task`, `login_user`, `register_user`.
- **TypeScript:** `camelCase` for hooks and handlers (`fetchAnalytics`, `handleSave`, `handleComplete`, `openCreateModal` in `frontend/src/components/TaskManager.tsx`; `initApp`, `reloadData` in `frontend/src/App.tsx`).

**Variables:**
- **Python:** `snake_case` (`db`, `current_user`, `task_in`, `status_filter` in `backend/routes/task_routes.py`).
- **TypeScript:** `camelCase` (`filterStatus`, `editingTask`, `isModalOpen` in `frontend/src/components/TaskManager.tsx`). Boolean state uses `is*`/`has*` prefix (`isOpen`, `isLogin`, `isAuthOpen`, `loading`).
- State setters always follow `const [x, setX] = useState(...)` (`frontend/src/App.tsx`, `frontend/src/components/*.tsx`).

**Types:**
- **Python:** Pydantic schemas in `backend/schemas.py` use `Base`-suffixed naming: `TaskBase` → `TaskCreate`, `TaskUpdate`, `TaskResponse`; auth has `UserCreate`, `UserLogin`, `UserResponse`, `Token`.
- **TypeScript:** `interface` names are plain domain nouns (`User`, `Task`, `AnalyticsData`, `MemoryItem`, `RAGResponse`) in `frontend/src/types.ts`; string-literal union types use `Type` suffix (`PriorityType`, `StatusType`). Component props use a local `interface Props` in each component file (see `frontend/src/components/TaskManager.tsx`, `CuteHeader.tsx`, `AuthModal.tsx`).

## Code Style

**Formatting:**
- **Python:** 4-space indentation, ~100 char lines, standard library imports first, then third-party, then local modules. No formatting tool (black/ruff) configured — no `.prettierrc`, no `setup.cfg`, no `pyproject.toml` exist. Formatting is manual.
- **TypeScript:** semicolons required and always present (`frontend/src/App.tsx`, all components, `frontend/src/services/api.ts`). Exceptions: `frontend/vite.config.ts` and `frontend/postcss.config.js` use no-semicolon style. No Prettier config exists.
- Quotes: single quotes everywhere in TS/TSX (`import { User } from '../types';`). No config file enforces this — it is a de-facto convention.

**Linting:**
- `frontend/package.json` defines `"lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"` but **no ESLint config file and no `eslint` dependency exist** — `npm run lint` currently fails. Before writing new frontend code, verify lint can run; if not, add `eslint` + a flat config (`eslint.config.js`) or remove the script.
- No Python linter configured.

**TypeScript strictness:**
- `frontend/tsconfig.json` sets `"strict": true`, `"noFallthroughCasesInSwitch": true`, but `noUnusedLocals` and `noUnusedParameters` are `false`. Keep `strict` mode on when writing new code; do not add `any` where a type is available.
- `App.tsx` passes `analytics?.current_streak_days || 4` — optional chaining with fallback is the established pattern for nullable data.

## Import Organization

**Python (`backend/routes/*.py`):**
1. Third-party framework imports (`from fastapi import APIRouter, Depends, HTTPException, status`, `from sqlalchemy.orm import Session`)
2. Standard library (`from typing import List, Optional`, `from datetime import datetime`)
3. Local modules — absolute, non-relative: `import models`, `import schemas`, `import auth`, `from database import get_db`, `import rag_service`

Example from `backend/routes/task_routes.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
import schemas
import auth
from database import get_db
import rag_service
```

**TypeScript (`frontend/src/**`):**
1. React/third-party (`import React, { useState } from 'react';`, `import axios from 'axios';`, lucide icons: `import { Plus, Check, Clock } from 'lucide-react';`)
2. Local relative imports, `../` style: `import { User, Task } from '../types';`, `import { TaskService } from '../services/api';`

**Path Aliases:**
- None. Frontend uses relative imports only (`../types`, `../services/api`). Vite proxy maps `/api` → `http://localhost:8000` in `frontend/vite.config.ts`; the frontend never references the backend URL directly (`const API_BASE = '/api'` in `frontend/src/services/api.ts`).

## Error Handling

**Backend — FastAPI `HTTPException`:**
- Raise `HTTPException(status_code=..., detail="...")` for expected failures. Recurring patterns:
  - 404 with `detail="Task not found"` — repeated verbatim in `backend/routes/task_routes.py` (`get_tasks` path at lines 67–69, `complete_task` 122–124, `delete_task` 150–152).
  - 400 `detail="Email address already registered."` in `backend/routes/auth_routes.py:13-17`.
  - 401 with `headers={"WWW-Authenticate": "Bearer"}` in `backend/auth.py:36-40` and `backend/routes/auth_routes.py:41-44`.
  - 400 `detail="Question cannot be empty."` in `backend/routes/rag_routes.py:17-18`.
- Use `status.HTTP_404_NOT_FOUND` style constants from `fastapi import status` where convenient, but raw literals (`status_code=404`, `status_code=400`) are also used — prefer `status.HTTP_*` constants for new code (`backend/routes/auth_routes.py` is the reference).
- Authentication dependency: `auth.get_current_user` (`backend/auth.py:35-51`) is injected via `Depends(...)` into every protected route and raises the 401 itself — routes do not re-check auth.

**Frontend — defensive try/catch with mock fallback:**
- `frontend/src/services/api.ts` wraps every axios call in `try/catch`; on failure it returns in-memory mock data instead of rethrowing (`catch (e) { return [...mockTasks]; }`). This is intentional (standalone preview mode) but means **frontend code cannot distinguish a failed API call from a successful mock response** — do not add error propagation logic that assumes the service layer throws.
- Components that need error display keep the try/catch locally: `AuthModal.tsx:36-37` does `catch (err: any) { setError(err.response?.data?.detail || 'Authentication failed...') }`.
- `AIAssistant.tsx:31-33` uses `catch (e) { console.error(e); }` — the only `console.*` usage in the frontend; prefer this over silent swallow for non-UI errors.
- `TaskManager.tsx:78-79` uses browser `prompt()`/`confirm()` for quick input — acceptable here, but modal-based forms are the established richer pattern.

## Logging

**Framework:** Python `logging` module; frontend uses `console.error` only.

**Patterns:**
- `backend/rag_service.py:32` creates a module logger: `logger = logging.getLogger("rag_service")`.
- Log levels used: `logger.warning` for import fallback (`rag_service.py:44`), `logger.error` for ChromaDB/store/API failures (`rag_service.py:124`, `172`, `275`, `292`, `314`), `logger.info` for expected Ollama fallback (`rag_service.py:253`).
- `backend/main.py:131` uses `print(f"Startup seeding error: {e}")` in the startup seed — a one-off; use `logger.error` in new code.
- No log formatting/configuration file exists; logging is default-config.

## Comments

**When to Comment:**
- Python: section divider comments with `# ---` banners (`backend/rag_service.py`: `# --- Vector Store Operations ---`, `# --- Multi-Agent Modules ---`; `backend/schemas.py`: `# --- Auth Schemas ---`), and `# ---` in `frontend/src/services/api.ts` (`// --- Mock Data Engine ... ---`). Match this style when adding sections.
- Purpose comments before non-obvious logic, e.g. `# Check if marked completed` in `backend/routes/task_routes.py:83`, `# --- Convert task creation to RAG Memory ---` at line 49.
- Frontend JSX: `{/* Section name */}` comments inside `frontend/src/components/*.tsx` (`{/* Filter & Search Bar */}`, `{/* Task Cards Grid */}` in `TaskManager.tsx`).

**JSDoc/TSDoc:**
- Not used anywhere in the frontend — no `/** */` doc comments on functions or components.
- Python: `backend/rag_service.py` is the only module with docstrings — a rich module-level docstring (lines 1–22) and short docstrings on `format_task_memory` (54–61), `store_memory` (103), and the agent classes (`RetrievalAgent` 141–143, `EvaluatorAgent` 194–197, `MultiLLMQueryAgent` 216–219). Route handlers and `backend/auth.py` functions have no docstrings.

## Function Design

**Size:** Route handlers are compact and single-purpose (auth routes 10–15 lines each in `backend/routes/auth_routes.py`). `backend/routes/analytics_routes.py` `get_analytics` is a 96-line monolith computing 11 metrics inline — do not extend it; extract metric helpers if adding analytics logic. `backend/rag_service.py` `_generate_smart_fallback` is a large keyword-branching function — keep branches as separate helpers when extending.

**Parameters:** FastAPI route handlers use `Depends()` for db session and current user as the last two params: `db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)` (`backend/routes/task_routes.py:14-19`). RAG pipeline functions use keyword-argument style calls (`backend/routes/rag_routes.py:20-26` passes `user_id=`, `user_name=`, `question=`, `provider=`, `model_name=`).

**Return Values:**
- Pydantic response models are declared on the decorator: `@router.get("", response_model=List[schemas.TaskResponse])`; the handler returns ORM objects directly and Pydantic serializes them (`from_attributes = True` in `backend/schemas.py`).
- Python functions without a meaningful result return `None` implicitly; `store_memory` returns the generated `mem_id` string (`backend/rag_service.py:102`).
- Frontend service methods return `Promise<T>` and annotate them (`async getTasks(): Promise<Task[]>` in `frontend/src/services/api.ts:136`). Component event handlers return `void`.

## Module Design

**Exports:**
- Backend: `router = APIRouter(prefix="/api/<area>", tags=["..."])` is the single export of every route module (`backend/routes/*.py`), registered in `backend/main.py:29-32` via `app.include_router(x_routes.router)`.
- Frontend: components use **named exports** (`export const TaskManager: React.FC<Props> = ...`). `frontend/src/App.tsx` has both a named export (`export const App`) and a default export (`export default App`) — `main.tsx` imports the default. Keep named exports for components; reserve default export for the app root.
- Services export const objects: `export const AuthService = {...}`, `TaskService`, `AnalyticsService`, `RAGService` from `frontend/src/services/api.ts`.
- Types export `interface`/`type` declarations from `frontend/src/types.ts`.

**Barrel Files:** None — components import from explicit paths (`import { CuteHeader } from './components/CuteHeader'`).

## React-Specific Conventions

- Function components typed `React.FC<Props>` (all six components). Props defined as local `interface Props` and destructured in the signature (`frontend/src/components/CuteHeader.tsx:15-23`).
- Hooks: `useState` + `useEffect` only; no custom hooks, no context, no router (tab switching via `useState<'tasks' | 'analytics' | 'assistant'>` in `frontend/src/App.tsx:13`).
- `useEffect(() => { fetchX(); }, [])` mount-and-fetch pattern in `App.tsx`, `AnalyticsDashboard.tsx`, `AIAssistant.tsx`.
- Tailwind utility classes with arbitrary hex values `bg-[#FFDFE5]` are used everywhere; the `tailwind.config.js` theme also defines semantic tokens (`cozy.rose`, `cozy.lavender`, `shadow-cozy`, `rounded-4xl`). Prefer theme tokens over raw arbitrary values in new code.
- `className` conditional logic uses template literals with ternaries (`TaskManager.tsx:192-194`, `CuteHeader.tsx:50-54`).
- Emojis in UI copy are a deliberate aesthetic convention (`🌸`, `🐱`, `🤖`) — keep for consistency.

## Security / Credential Conventions

- `backend/auth.py:12` has a hardcoded default JWT secret fallback: `SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cozy_rag_productivity_tracker_super_secret_key_2026")`. Set `JWT_SECRET_KEY` in production; never rely on the fallback.
- `backend/main.py:38-44` seeds a demo user with hardcoded password `cozy123` — demo-only credentials, not for production data.
- Frontend stores the JWT in `localStorage` under `cozy_token` (`frontend/src/services/api.ts:14, 98`) and attaches it via an axios request interceptor (lines 13–19) — the single auth wiring point.
- LLM API keys are read from env vars at call time (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`/`XAI_API_KEY` in `backend/rag_service.py:257-314`) — never hardcode keys. No `.env` file is committed; `.env` is gitignored.

---

*Convention analysis: 2026-08-11*
