<div align="center">

# 🌸 Cozy AI Productivity & RAG Intelligence System

**A full-stack productivity tracker with a cute & cozy pastel UI, 11 analytics metrics, and a grounded RAG task-memory assistant.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-FF4F00?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗 System Architecture](#-system-architecture)
- [🧰 Tech Stack](#-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Getting Started](#-getting-started)
- [🐳 Production Deployment with Docker Compose](#-production-deployment-with-docker-compose)
- [🔑 Environment Variables](#-environment-variables)
- [🔌 API Reference](#-api-reference)
- [🧠 Grounded RAG Task Memory Engine](#-grounded-rag-task-memory-engine)
- [🧪 Testing & Quality Gates](#-testing--quality-gates)
- [🔄 CI/CD Pipeline](#-cicd-pipeline)
- [🛠 Troubleshooting](#-troubleshooting)

---

## 📋 Overview

Cozy AI is a production-ready **AI Productivity System** that combines:

- A **Cute & Cozy Soft Pastel UI** (inspired by PixelBrew Studio's *Cozy Habit Tracker*) built with React, TypeScript, and Tailwind CSS.
- A **strict 2-table relational schema** (`users` + `tasks`) managed with Alembic migrations.
- **11 productivity analytics metrics** computed in real time with SQL aggregation plus Python-derived streak and distribution data.
- A **Grounded RAG Task Memory Subsystem** that ingests every task lifecycle event into a per-user vector store and answers natural-language questions about your work — with citations, prompt-injection defense, and multi-provider LLM support.
- A **production Docker Compose stack** (PostgreSQL 16 + FastAPI + Nginx-served React) with health checks and a GitHub Actions CI pipeline.

> **Version:** 2.1.0 · **Status:** Active

---

## ✨ Key Features

### 🎨 Cute & Cozy UI
- Soft pastel palette (`#FFDFE5`, `#FAF6F0`, `#EDE9FE`), pill-shaped badges, rounded cards, and fully responsive components.
- Three-tab SPA experience: **Tasks**, **Analytics Dashboard**, and **AI Assistant**.
- Thoughtful touches throughout: selection colors, hover states, and a footer with tech-stack badges.

### 🗄 Relational Data Model (2 Tables)
| Table | Columns |
|---|---|
| `users` | `id`, `name`, `email`, `password_hash`, `created_at` |
| `tasks` | `id`, `user_id`, `title`, `description`, `priority`, `status`, `due_date`, `created_at`, `completed_at`, `estimated_minutes`, `actual_minutes` |

### 📊 11 Analytics Metrics
Real-time computation: counts are pushed to SQL aggregation (daily completions, weekly completions, monthly progress %, completion rate %, total/completed/pending/overdue counts, high-priority completion %, average completion time), with **streak tracking** and **weekday / hour-of-day completion distributions** derived from completed-task timestamps (visualized with Recharts).

### 🧠 Natural Language RAG Memory Engine
- **Lifecycle event ingestion** — `CREATE`, `UPDATE`, `COMPLETE`, `DELETE`, `DELAY`, `HISTORICAL_LOG` — each task action is embedded into memory.
- **User-scoped vector store** — ChromaDB with `SentenceTransformers` (`all-MiniLM-L6-v2`) embeddings, strictly isolated per user.
- **Hybrid retrieval** — semantic similarity + lexical token matching + metadata filtering.
- **Deterministic 4-factor reranking** — semantic + lexical + metadata match + 30-day recency decay.
- **Grounded generation** — answers must cite their sources (`[Source: <id>]`), with strict context bounding and prompt-injection isolation.
- **Multi-provider LLM integration** — **Ollama** (local default), **OpenAI**, **Google Gemini**, and **xAI Grok**.

### 🔐 Auth & Security
- JWT (HS256) authentication with bcrypt password hashing.
- **Server-side logout** via a token blacklist — revoked tokens can never be reused.
- **Change-password** flow that verifies the current password.
- In-process **sliding-window rate limiting** on auth and RAG endpoints.
- Per-provider **model allowlist** to prevent LLM cost abuse.
- Per-user **RAG answer cache** (TTL-bounded) to cut latency and spend.

### 🐳 Production-Ready Deployment
- PostgreSQL 16 service with persistent volume and health checks.
- Multi-stage frontend build served by Nginx, reverse-proxying `/api/*` → `backend:8000`.
- GitHub Actions CI: lint, typecheck, offline tests, Docker builds, and Compose smoke tests.

---

## 🏗 System Architecture

```
                                +-------------------+
                                |   React + Vite    |
                                |  (Frontend SPA)   |
                                +---------+---------+
                                          |
                                          | HTTP / Nginx Proxy
                                          v
                                +-------------------+
                                |      FastAPI      |
                                |  (Backend API)    |
                                +----+---------+----+
                                     |         |
                      SQLAlchemy ORM |         | ChromaDB Client
                                     v         v
                         +---------------+  +------------------+
                         | PostgreSQL 16 |  | Vector Store DB  |
                         |  (Relational) |  |   (ChromaDB)     |
                         +---------------+  +------------------+
```

The backend additionally integrates with an LLM provider (Ollama by default) for grounded generation. Every RAG query flows through: **hybrid retrieval → 4-factor reranking → bounded context construction → grounded generation with citation enforcement**.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript 5.2, Vite 5, Tailwind CSS 3, Recharts 2, Axios, lucide-react |
| **Backend** | Python 3.11+, FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2, Alembic |
| **Database** | PostgreSQL 16 (prod / Docker), SQLite (dev default) |
| **Vector Store** | ChromaDB 0.5 + SentenceTransformers (`all-MiniLM-L6-v2`) |
| **LLM Providers** | Ollama (`llama3`), OpenAI (`gpt-3.5-turbo`), Gemini (`gemini-1.5-flash`), Grok (`grok-beta`) |
| **Auth** | PyJWT (HS256), bcrypt, server-side token blacklist |
| **Testing** | Pytest + pytest-cov (backend), Vitest + Testing Library (frontend) |
| **Infra** | Docker Compose, Nginx, GitHub Actions |

---

## 📁 Project Structure

```
.
├── backend/                  # FastAPI application
│   ├── alembic/              # Database migrations
│   ├── core/                 # Config, logging, rate limiting
│   ├── routes/               # API routers (auth, tasks, analytics, rag, health)
│   ├── services/rag/         # RAG pipeline (retrieval, reranking, grounding, memory)
│   │   └── providers/        # LLM providers (ollama, openai, gemini, grok)
│   ├── tests/                # Backend test suite (offline & deterministic)
│   ├── auth.py               # JWT creation/verification, password hashing
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   └── main.py               # FastAPI app entry point
├── frontend/                 # React + Vite SPA
│   └── src/
│       ├── components/       # CuteHeader, AuthModal, TaskManager, AnalyticsDashboard, AIAssistant
│       ├── services/         # Axios API client
│       └── utils/            # Date helpers
├── .github/workflows/        # GitHub Actions CI
├── docker-compose.yml        # Production stack (PostgreSQL + backend + frontend)
├── .env.example              # Environment variable template
├── setup.py                  # One-command environment setup
└── start.py                  # One-command dev launcher (backend + frontend + browser)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (with npm)
- For RAG queries: a running LLM backend. The default is **Ollama** — install it and pull a model:

```bash
ollama pull llama3
```

> Using OpenAI / Gemini / Grok instead? Set `RAG_PROVIDER` and the matching API key (see [Environment Variables](#-environment-variables)).

### ⚡ Quick Start (Automated)

The project ships two helper scripts that handle everything:

```bash
# 1. One-time setup: venv, deps, .env, migrations
python setup.py

# 2. Launch backend + frontend, wait for health, open the browser
python start.py
```

### 🖥 Manual Setup

#### 1. Backend (FastAPI)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows (PowerShell):  .\venv\Scripts\Activate.ps1
# Linux/macOS:           source venv/bin/activate

# Install dependencies (add [dev] extras for pytest/ruff/mypy)
pip install -e ".[dev]"

# Apply database migrations
alembic upgrade head

# Run the dev server
uvicorn main:app --reload --port 8000
```

> Interactive API documentation: **http://localhost:8000/docs**
>
> Migrations also run automatically on application startup (development falls back to `create_all` if no Alembic state exists yet).

#### 2. Frontend (React + Vite)

```bash
cd frontend
npm ci          # install dependencies
npm run dev     # start dev server
```

> The SPA runs at **http://localhost:3000** and proxies `/api/*` to the backend on port 8000.

#### 🌱 Demo Data (Optional)

Set `SEED_DEMO=true` in your `.env` to seed a demo user and sample tasks + RAG memories on startup (development only):

- **Email:** `demo@cozy.app`
- **Password:** `cozy123`

---

## 🐳 Production Deployment with Docker Compose

Deploy the complete stack (PostgreSQL, FastAPI backend, Nginx-served frontend) with health checks and automatic migrations:

```bash
# 1. Create .env from the template (JWT_SECRET_KEY is required)
cp .env.example .env

# 2. Generate a strong JWT secret and put it in .env
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 3. Build and start the stack
docker compose up --build -d
```

| Service | URL |
|---|---|
| **Frontend Application** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health — Liveness** | http://localhost:8000/health/live |
| **Health — Readiness** | http://localhost:8000/health/ready |

To shut down:

```bash
docker compose down
```

> **Security notes:** `docker-compose.yml` fails fast if `JWT_SECRET_KEY` is unset. The demo seed is disabled in production. The backend container runs as a non-root user, and Nginx sends security headers (CSP, X-Frame-Options, nosniff) to mitigate XSS and token exfiltration.

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` in the project root and adjust as needed. `*_API_KEY` values are only required when the corresponding provider is selected.

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development`, `test`, `production`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | `text` | Log format (`text` or `json`) |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./cozy_productivity.db` | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | *(required in prod)* | JWT signing secret. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token lifetime in minutes (7 days) |
| `SEED_DEMO` | `false` | Seed demo user/tasks on startup (non-prod only) |
| `CORS_ORIGINS` | `["http://localhost:3000", ...]` | Allowed frontend origins (JSON array) |
| `RAG_PROVIDER` | `ollama` | Default LLM provider (`ollama`, `openai`, `gemini`, `grok`) |
| `CHROMA_PATH` | `./chroma_db` | Vector store directory |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformers embedding model |
| `RAG_TOP_K` | `8` | Candidate documents retrieved |
| `RAG_RERANK_LIMIT` | `5` | Documents kept after reranking |
| `RAG_RELEVANCE_THRESHOLD` | `0.25` | Minimum relevance to include a source |
| `RAG_MAX_CONTEXT_CHARS` | `4000` | Max context characters sent to the LLM |
| `RAG_MAX_SOURCES` | `5` | Max sources cited in an answer |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service endpoint |
| `OLLAMA_MODEL` | `llama3` | Default Ollama model |
| `LLM_TIMEOUT_SECONDS` | `10.0` | LLM request timeout |
| `LLM_MAX_RETRIES` | `1` | LLM retry count on transient failure |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | — / `gpt-3.5-turbo` | OpenAI credentials & model |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | — / `gemini-1.5-flash` | Google Gemini credentials & model |
| `GROK_API_KEY` / `GROK_MODEL` | — / `grok-beta` | xAI Grok credentials & model |
| `RATE_LIMIT_ENABLED` | `true` | Enable in-process rate limiting |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `20` | Max auth attempts per IP per minute |
| `RATE_LIMIT_RAG_PER_MINUTE` | `30` | Max RAG queries per IP per minute |
| `RATE_LIMIT_GENERAL_PER_MINUTE` | `120` | Max general requests per IP per minute |
| `RAG_CACHE_ENABLED` | `true` | Cache identical RAG questions per user |
| `RAG_CACHE_TTL_SECONDS` | `300` | Answer cache TTL |
| `RAG_CACHE_MAX_ENTRIES` | `128` | Answer cache size limit |

> **Security:** Production refuses to start without `JWT_SECRET_KEY`. Auth endpoints are rate-limited, JWTs are revoked server-side on logout, the LLM model name is validated against a per-provider allowlist, and rate limiting is disabled automatically under `APP_ENV=test`.

---

## 🔌 API Reference

All endpoints (except auth & health) require a `Authorization: Bearer <token>` header. Interactive docs are available at `/docs`.

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health/live` | Liveness probe (always 200 when the process is up) |
| `GET` | `/health/ready` | Readiness probe (checks DB connectivity + vector store mode) |

### Auth (`/api/auth`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new user → returns JWT + user |
| `POST` | `/api/auth/login` | Login with email/password → returns JWT + user |
| `GET` | `/api/auth/me` | Get the current user's profile |
| `POST` | `/api/auth/logout` | Revoke the current token server-side (blacklist) |
| `POST` | `/api/auth/change-password` | Change password after verifying the current one |

### Tasks (`/api/tasks`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tasks` | List tasks — filters: `status`, `priority`, `limit` (≤1000), `offset` |
| `GET` | `/api/tasks/{id}` | Get a single task |
| `POST` | `/api/tasks` | Create a task (ingests a `CREATE` memory) |
| `PUT` | `/api/tasks/{id}` | Update a task (ingests `UPDATE` / `DELAY` / `COMPLETE` memory) |
| `PATCH` / `PUT` | `/api/tasks/{id}/complete` | Mark complete, optional `?actual_minutes=` |
| `DELETE` | `/api/tasks/{id}` | Delete a task (ingests a `DELETE` memory) |

### Analytics (`/api/analytics`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics` | All 11 productivity metrics for the current user |

### RAG AI Assistant (`/api/rag`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/rag/query` | Ask a natural-language question with grounded, cited answers. Optional `provider` / `model_name` body fields (validated against allowlist) |
| `GET` | `/api/rag/memories` | List stored memories — filters: `limit`, `offset`, `task_id`, `action` |
| `DELETE` | `/api/rag/memories/{id}` | Delete a specific memory |

---

## 🧠 Grounded RAG Task Memory Engine

### Memory Lifecycle

Every task creation, modification, completion, delay, or deletion generates a structured natural-language memory vector:

- **CREATE** — `Created task '<title>' with priority <priority> due on <date>.`
- **COMPLETE** — `Completed task '<title>' in <actual> mins (estimated: <est> mins).`
- **DELAY** — `Postponed task '<title>'; due date moved from <old> to <new>.`
- **DELETE** — `Deleted task '<title>' on <timestamp>.`
- **HISTORICAL_LOG** — free-form context injected at seed time.

### Pipeline Execution Flow

1. **User-scoped hybrid retrieval** — ChromaDB vectors are filtered strictly by `user_id` + metadata tags, then scored with combined semantic similarity and lexical overlap.
2. **4-factor deterministic reranking** —
   - Semantic similarity: weight **0.50**
   - Lexical token match: weight **0.25**
   - Metadata relevance: weight **0.15**
   - 30-day linear recency decay: weight **0.10**
3. **Bounded context construction** — enforces `RAG_MAX_SOURCES` (5) and `RAG_MAX_CONTEXT_CHARS` (4000) to prevent prompt overflow.
4. **Grounded generation & citation enforcement** — the LLM answers strictly from provided context blocks; every claim must include `[Source: <id>]`.
5. **Prompt-injection defense** — retrieved memory content is labeled as untrusted data in the system prompt to prevent instruction-override attacks.

---

## 🧪 Testing & Quality Gates

The backend suite is **100% deterministic and offline** (in-memory DBs, no network calls, no external APIs, no disk writes).

```bash
cd backend
pytest --cov=. --cov-fail-under=70    # tests + coverage gate
ruff check .                          # lint
mypy                                  # typecheck
```

Coverage areas:

- Authentication & JWT security (`test_auth.py`)
- Task CRUD & cross-user authorization (`test_tasks.py`)
- Analytics calculations & date handling (`test_analytics.py`)
- Liveness & readiness health checks (`test_health.py`)
- RAG pipeline, retrieval, citation, injection defense & benchmark evaluation (`test_rag.py`)
- Security regression tests — logout revocation, change-password, model allowlist, rate limits (`test_security.py`)

Frontend:

```bash
cd frontend
npm run lint        # ESLint (zero warnings)
npm run typecheck   # tsc --noEmit
npm run test        # Vitest
npm run build       # production build
```

---

## 🔄 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. **Backend CI** — Python 3.11 setup, dependency install (`./backend[dev]`), Ruff lint, MyPy typecheck, Pytest with ≥70% coverage.
2. **Frontend CI** — Node 20 setup, `npm ci`, ESLint, TypeScript typecheck, Vitest, production build.
3. **Docker smoke test** — builds the full Compose stack, polls service health, then runs end-to-end API checks (register → create task → complete → RAG query).

---

## 🛠 Troubleshooting

### Database migration issues

If schema state gets out of sync during development:

```bash
cd backend
alembic stamp head
alembic check
```

### Docker container connection issues

The frontend reaches the backend via the Docker network hostname (`http://backend:8000`), not `localhost`. Check container logs:

```bash
docker compose logs backend
docker compose logs frontend
```

### RAG returns no usable sources

- Confirm Ollama is running: `curl http://localhost:11434/api/tags`
- Pull the configured model: `ollama pull llama3`
- Create or complete a task first — memories are ingested from task lifecycle events.
- Check the readiness endpoint — if `rag_vector_store` reports `in-memory-fallback`, the persistent ChromaDB backend is unavailable and retrieval falls back to an in-memory store.

---

*Made with 💖 for high productivity.*
