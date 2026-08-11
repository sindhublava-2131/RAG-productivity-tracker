# Technology Stack

**Analysis Date:** 2026-08-11

## Languages

**Primary:**
- Python 3.11 - Backend API and RAG engine (`backend/`). `requires-python = ">=3.11"` in `backend/pyproject.toml`; runtime pinned by `backend/Dockerfile` (`FROM python:3.11-slim`)
- TypeScript 5.2+ - Frontend application (`frontend/`), strict mode, `jsx: react-jsx` (`frontend/tsconfig.json`)

**Secondary:**
- HTML - `frontend/index.html` (Vite entry)
- CSS - `frontend/src/index.css` (Tailwind directives + cozy custom styles/animations)

## Runtime

**Environment:**
- Node.js 20 (Alpine) - Frontend build stage in `frontend/Dockerfile` (`FROM node:20-alpine`)
- Python 3.11 (slim) - Backend runtime in `backend/Dockerfile`
- Uvicorn ~0.30.0 - ASGI server (`backend/pyproject.toml`; `backend/Dockerfile` CMD `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000`)
- nginx:alpine - Frontend static server in production (`frontend/Dockerfile`, `frontend/nginx.conf`)

**Package Manager:**
- npm - Frontend (`frontend/package-lock.json` present, committed; Docker uses `npm ci`)
- pip (editable install) - Backend via `backend/requirements.txt` containing `-e .`, driven by `backend/pyproject.toml` (setuptools build backend)

## Frameworks

**Core:**
- FastAPI ~0.115.0 - Backend web framework (`backend/main.py`), lifespan-based startup, CORS middleware, 5 routers
- React 18.2+ - Frontend UI (`frontend/src/App.tsx`, `frontend/src/main.tsx`)
- SQLAlchemy 2.0.30+ - ORM (`backend/database.py` engine/session, `backend/models.py` schema)
- Pydantic 2.8+ / pydantic-settings 2.4+ - Validation + centralized config (`backend/schemas.py`, `backend/core/config.py`)
- Alembic ~1.13.0 - Database migrations (`backend/alembic/`, `backend/alembic/versions/0001_initial.py`)
- PyJWT ~2.9.0 - JWT encode/decode for auth (`backend/auth.py`)
- bcrypt ~4.2.0 - Password hashing (`backend/auth.py`)

**RAG / ML:**
- chromadb ~0.5.0 - Persistent vector store (`backend/services/rag/vector_store.py`)
- sentence-transformers ~3.0.0 - Embedding model `all-MiniLM-L6-v2` (`backend/services/rag/embeddings.py`)
- httpx ~0.27.0 - Async HTTP client for LLM providers (`backend/services/rag/providers/_http.py`)

**Testing / Quality:**
- pytest ~8.3.0 + pytest-cov - Backend tests (`backend/tests/`, configured in `backend/pyproject.toml`)
- ruff ~0.5.0 - Backend linter (configured in `backend/pyproject.toml`)
- mypy ~1.10.0 - Backend type checker (configured in `backend/pyproject.toml`)
- vitest ~1.6.0 + @testing-library/react + jsdom - Frontend tests (`frontend/src/**/*.test.ts(x)`, config in `frontend/vite.config.ts`)
- ESLint 8 + typescript-eslint - Frontend linting (`frontend/.eslintrc.cjs`)

**Build/Dev:**
- Vite 5.2+ - Dev server + bundler (`frontend/vite.config.ts`; dev port 3000, proxies `/api` → `http://localhost:8000`)
- @vitejs/plugin-react 4.2+ - React plugin
- Tailwind CSS 3.4+ - Styling (`frontend/tailwind.config.js` custom `cozy` theme palette)
- PostCSS + autoprefixer - CSS pipeline (`frontend/postcss.config.js`)
- Docker / Docker Compose - Orchestration (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`)

## Key Dependencies

**Critical (backend):**
- chromadb ~0.5.0 - Persistent vector store for RAG memories (`backend/services/rag/vector_store.py`)
- sentence-transformers ~3.0.0 - Embedding model `all-MiniLM-L6-v2` (`backend/services/rag/embeddings.py`)
- PyJWT ~2.9.0 - JWT encode/decode (`backend/auth.py`)
- bcrypt ~4.2.0 - Password hashing (`backend/auth.py`)
- psycopg2-binary ~2.9.9 - PostgreSQL driver (production `docker-compose.yml`)
- orjson ~3.10.0 - Fast JSON serialization

**Frontend:**
- axios ^1.6.8 - HTTP client (`frontend/src/services/api.ts`)
- recharts ^2.12.3 - Analytics charts (`frontend/src/components/AnalyticsDashboard.tsx`)
- lucide-react ^0.363.0 - Icons throughout `frontend/src/components/`
- clsx ^2.1.0 + tailwind-merge ^2.2.2 - Class-name composition

**Infrastructure:**
- email-validator ~2.2.0 - Email validation for `EmailStr` (`backend/schemas.py`)
- python-multipart ~0.0.9 - Required by FastAPI OAuth2 form handling

## Configuration

**Environment:**
- No `.env` file in the repo (`.env` is gitignored); `.env.example` is referenced by README/setup but not committed
- All env vars read centrally via pydantic-settings in `backend/core/config.py` (single `settings` object; code must not call `os.getenv` directly)
- Key vars: `APP_ENV`, `DATABASE_URL`, `JWT_SECRET_KEY`, `SEED_DEMO`, `CORS_ORIGINS`, `RAG_PROVIDER`, `OLLAMA_HOST`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`, `LLM_TIMEOUT_SECONDS`, `RAG_TOP_K`, `RAG_RERANK_LIMIT`, `RAG_RELEVANCE_THRESHOLD`, `RAG_MAX_CONTEXT_CHARS`, `RAG_MAX_SOURCES`
- `JWT_SECRET_KEY` is **required in production** (fails fast via validator in `backend/core/config.py`); in development an ephemeral random secret is generated per-process (`secrets.token_urlsafe(48)`) — no hardcoded default anywhere

**Build:**
- `frontend/vite.config.ts` - dev port 3000, `/api` proxy to `localhost:8000`, vitest `test` block (jsdom, setup file)
- `frontend/tsconfig.json` - ES2020, bundler resolution, `strict: true`
- `frontend/tailwind.config.js` - cozy pastel design tokens (`cozy.*` colors, `shadow-cozy`, `rounded-4xl/5xl`, Fredoka/Quicksand font stack)
- `frontend/.eslintrc.cjs` - ESLint 8 + typescript-eslint + react-hooks + react-refresh
- `backend/pyproject.toml` - project metadata, deps, `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.setuptools.packages.find]`
- `backend/alembic.ini` - Alembic config (`script_location = alembic`)
- `docker-compose.yml` - service definitions, env overrides, named volumes, healthchecks

**Linting:**
- Backend: `ruff check .` (selects `E, F, W, I, UP, B, ASYNC`, line-length 110, per-file ignores for `B008` in auth/routes and `E402` in alembic)
- Backend typecheck: `mypy --config-file pyproject.toml` (pydantic plugin)
- Frontend: `npm run lint` (`eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0`), `npm run typecheck` (`tsc --noEmit`)

## Platform Requirements

**Development:**
- Python 3.11+ with `pip install -r backend/requirements.txt` (editable install from `pyproject.toml`)
- Node 20+ with `npm ci` (`frontend/package.json`)
- Ollama running locally at `http://localhost:11434` for RAG answers (optional; graceful degradation exists)
- sentence-transformers downloads `all-MiniLM-L6-v2` from HuggingFace on first use (lazy load; falls back to deterministic lightweight embeddings offline)
- One-command setup/launch helpers: `python setup.py` (venv, deps, migrations, npm install) and `python start.py` (starts backend on 8000 + frontend on 3000, opens browser)

**Production:**
- Docker Desktop; `docker compose up --build -d` per `docker-compose.yml` (PostgreSQL 16 + backend + nginx frontend, healthchecks on all services)
- Backend: port 8000; Frontend: port 3000 → nginx container port 80
- `JWT_SECRET_KEY` must be supplied (production fail-fast); DB schema managed by Alembic (`alembic upgrade head` in Docker CMD)

---

*Stack analysis: 2026-08-11*
