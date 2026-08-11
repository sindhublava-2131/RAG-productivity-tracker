# Technology Stack

**Analysis Date:** 2026-08-11

## Languages

**Primary:**
- Python 3.11 - Backend API and RAG engine (`backend/`). Pinned by `backend/Dockerfile` (`FROM python:3.11-slim`)
- TypeScript 5.9.3 - Frontend application (`frontend/`), strict mode, `jsx: react-jsx`

**Secondary:**
- HTML - `frontend/index.html` (Vite entry)
- CSS - `frontend/src/index.css` (Tailwind directives + base styles)

## Runtime

**Environment:**
- Node.js 18 (Alpine) - Frontend build stage in `frontend/Dockerfile`
- Python 3.11 (slim) - Backend runtime in `backend/Dockerfile`
- Uvicorn >= 0.22.0 - ASGI server (`backend/requirements.txt`, `backend/Dockerfile` CMD `uvicorn main:app --host 0.0.0.0 --port 8000`)

**Package Manager:**
- npm - Frontend (`frontend/package-lock.json` present, committed)
- pip - Backend (`backend/requirements.txt`; no lockfile, no `pyproject.toml`/`setup.py`)

## Frameworks

**Core:**
- FastAPI >= 0.100.0 - Backend web framework (`backend/main.py`), with CORS middleware, 4 routers under `/api`
- React 18.3.1 - Frontend UI (`frontend/src/App.tsx`, `frontend/src/main.tsx`)
- SQLAlchemy 2.x - ORM (`backend/database.py` engine/session, `backend/models.py` schema)
- Pydantic 2.x - Request/response validation (`backend/schemas.py`)

**Testing:**
- pytest >= 7.4.0 - Declared in `backend/requirements.txt`; no test files or config detected anywhere in the repo

**Build/Dev:**
- Vite 5.4.21 - Dev server + bundler (`frontend/vite.config.ts`; dev port 3000, proxies `/api` → `http://localhost:8000`)
- @vitejs/plugin-react 4.7.0 - React plugin
- Tailwind CSS 3.4.19 - Styling (`frontend/tailwind.config.js` custom `cozy` theme palette)
- PostCSS 8.5.26 + autoprefixer 10.5.4 - CSS pipeline (`frontend/postcss.config.js`)
- Docker / Docker Compose - Orchestration (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`)

## Key Dependencies

**Critical:**
- chromadb >= 0.4.0 - Persistent vector store for RAG memories (`backend/rag_service.py`, path `./chroma_db`)
- sentence-transformers >= 2.2.2 - Embedding model `all-MiniLM-L6-v2` (`backend/rag_service.py`)
- python-jose[cryptography] >= 3.3.0 - JWT encode/decode for auth (`backend/auth.py`)
- passlib[bcrypt] >= 1.7.4 - Password hashing (`backend/auth.py`)
- axios (^1.6.8) - Frontend HTTP client (`frontend/src/services/api.ts`)
- recharts 2.15.4 - Analytics charts (`frontend/src/components/AnalyticsDashboard.tsx`)
- lucide-react 0.363.0 - Icons throughout `frontend/src/components/`
- clsx ^2.1.0 + tailwind-merge ^2.2.2 - Class-name composition

**Infrastructure:**
- requests >= 2.31.0 - Direct HTTP calls to LLM providers (`backend/rag_service.py`)
- python-multipart >= 0.0.6 - Required by FastAPI OAuth2 password form (`backend/auth.py`)

## Configuration

**Environment:**
- No `.env` files present in the repo (`.env` is gitignored in `.gitignore`)
- Env vars read in `backend/database.py` (`DATABASE_URL`) and `backend/auth.py` (`JWT_SECRET_KEY`), `backend/rag_service.py` (`OLLAMA_HOST`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`/`XAI_API_KEY`)
- Values documented in `README.md` table; defaults hardcoded in code (see INTEGRATIONS.md)

**Build:**
- `frontend/vite.config.ts` - dev port 3000, `/api` proxy to backend
- `frontend/tsconfig.json` - ES2020, bundler resolution, strict
- `frontend/tailwind.config.js` - cozy pastel design tokens
- `frontend/postcss.config.js` - tailwindcss + autoprefixer plugins
- `docker-compose.yml` - service definitions, env overrides, volume mounts (`./backend/chroma_db`, `./backend/cozy_productivity.db`), `host.docker.internal` gateway for Ollama

**Linting:**
- `frontend/package.json` declares a `lint` script (`eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0`) but no ESLint config file (`.eslintrc*`/`eslint.config.*`) was found in the repo — `npm run lint` will fail without one

## Platform Requirements

**Development:**
- Python 3.11+ with `pip install -r requirements.txt` (`backend/requirements.txt`)
- Node 18+ with `npm install` (`frontend/package.json`)
- Ollama running locally at `http://localhost:11434` for RAG answers (optional; fallback rule engine exists)
- Sentence-transformers downloads `all-MiniLM-L6-v2` from HuggingFace on first run

**Production:**
- Docker Desktop; `docker-compose up --build` per `docker-compose.yml`
- Backend: port 8000; Frontend served by nginx:alpine on port 3000 (container port 80)
- Local-only deployment — no cloud hosting configuration detected

---

*Stack analysis: 2026-08-11*
