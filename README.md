# 🌸 Cozy AI Productivity & RAG Task Memory Intelligence System

A high-performance, production-ready AI Productivity System featuring a **Cute & Cozy Soft Pastel UI** (inspired by PixelBrew Studio's *Cozy Habit Tracker*), strict **2-Table Database Architecture**, **11 Productivity Analytics Metrics**, **Alembic Database Migrations**, **Production Docker Compose Stack**, and a **Grounded RAG Task Memory Subsystem**.

---

## 🌟 Key Features

1. **Cute & Cozy Soft Pastel Aesthetic**: Soft pastel color palette (`#FFDFE5`, `#FAF6F0`, `#EDE9FE`), pill-shaped badges, rounded card layouts, and responsive components.
2. **2-Table Relational Schema**:
   - `users` (`id`, `name`, `email`, `password_hash`, `created_at`)
   - `tasks` (`id`, `user_id`, `title`, `description`, `priority`, `status`, `due_date`, `created_at`, `completed_at`, `estimated_minutes`, `actual_minutes`)
3. **11 Analytics Metrics**: Real-time computation of daily/weekly completions, monthly progress %, completion rate %, task breakdown, priority completion %, average duration, streak tracking, and weekday/hour distribution.
4. **Natural Language RAG Memory Engine**:
   - Lifecycle event ingestion (`CREATE`, `UPDATE`, `COMPLETE`, `DELETE`, `DELAY`, `HISTORICAL_LOG`).
   - Scoped vector store (`ChromaDB`) with `SentenceTransformers` (`all-MiniLM-L6-v2`) embeddings.
   - User-isolated hybrid retrieval (semantic similarity + lexical token matching + metadata filtering).
   - Deterministic 4-factor reranking (semantic + lexical + metadata match + 30-day recency decay).
   - Strict context length bounding and source deduplication.
   - Grounded generation with citation validation (`[Source: <id>]`) and prompt injection isolation.
   - Multi-provider LLM integration (**Ollama** local default, **OpenAI**, **Google Gemini**, **xAI Grok**).
5. **Production Dockerization & CI/CD**:
   - PostgreSQL 16 database service with persistent volume and healthchecks.
   - Multi-stage frontend build with Nginx reverse proxying (`/api/*` -> `backend:8000`).
   - GitHub Actions CI workflow covering linting, typechecking, offline tests, Docker builds, and Compose smoke tests.

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

---

## 🚀 Getting Started

### Local Development Setup

#### 1. Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run dev server
uvicorn main:app --reload --port 8000
```
> Interactive API Documentation is available at `http://localhost:8000/docs`.

#### 2. Frontend Setup (React + Vite)

```bash
cd frontend

# Install Node dependencies
npm ci

# Start development server
npm run dev
```
> The frontend application runs at `http://localhost:3000`.

---

## 🐳 Production Deployment with Docker Compose

Deploy the complete stack (PostgreSQL, FastAPI Backend, Nginx Frontend) with health checks and automatic migrations:

```bash
docker compose up --build -d
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Health Check Endpoints**:
  - `http://localhost:8000/health/live`
  - `http://localhost:8000/health/ready`

To shut down the stack:

```bash
docker compose down
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` in the project root:

| Variable | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development`, `test`, `production`) |
| `DATABASE_URL` | `postgresql://cozy:cozy_pass@db:5432/cozy_db` | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | *(Required in Production)* | Secret key for signing JWT tokens |
| `SEED_DEMO` | `false` | Enable seed demo user/tasks on startup (non-prod only) |
| `RAG_PROVIDER` | `ollama` | Default LLM provider (`ollama`, `openai`, `gemini`, `grok`) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service endpoint |
| `OPENAI_API_KEY` | *(Optional)* | OpenAI API key |
| `GEMINI_API_KEY` | *(Optional)* | Google Gemini API key |
| `GROK_API_KEY` | *(Optional)* | xAI Grok API key |

---

## 🧠 Grounded RAG Task Memory Engine

### Memory Lifecycle

Every task creation, modification, completion, delay, or deletion generates a structured natural-language memory vector:

- **CREATE**: `Created task '<title>' with priority <priority> due on <date>.`
- **COMPLETE**: `Completed task '<title>' in <actual> mins (estimated: <est> mins).`
- **DELAY**: `Postponed task '<title>'; due date moved from <old> to <new>.`
- **DELETE**: `Deleted task '<title>' on <timestamp>.`

### Pipeline Execution Flow

1. **User-Scoped Hybrid Retrieval**: Filters ChromaDB vectors strictly by `user_id` and metadata tags, scoring candidates with combined semantic similarity and lexical overlap.
2. **4-Factor Reranking**: Evaluates candidates based on:
   - Semantic similarity ($w=0.50$)
   - Lexical token match ($w=0.25$)
   - Metadata relevance ($w=0.15$)
   - 30-day linear recency decay ($w=0.10$)
3. **Bounded Context Construction**: Enforces `RAG_MAX_SOURCES` ($5$) and `RAG_MAX_CONTEXT_CHARS` ($4000$) limits to prevent prompt overflow.
4. **Grounded Generation & Citation Enforcement**: The LLM generates answers strictly from provided context blocks. Every statement based on retrieved memory must include `[Source: <id>]`.
5. **Prompt Injection Defense**: Retrieved memory content is labeled as untrusted data in system prompts to prevent instruction override attacks.

---

## 🧪 Testing & Evaluation

### Backend Tests & RAG Evaluation Benchmark

The backend test suite is 100% deterministic and offline, using in-memory databases and fakes (no network calls, external APIs, or disk writes required).

```bash
cd backend
pytest
```

Includes test suites for:
- Authentication & JWT token security (`test_auth.py`)
- Task CRUD & Cross-user authorization (`test_tasks.py`)
- Analytics calculations & date handling (`test_analytics.py`)
- Liveness & Readiness health checks (`test_health.py`)
- RAG pipeline, retrieval, citation, injection defense & benchmark evaluation (`test_rag.py`)
- Security regression tests (`test_security.py`)

### Frontend Tests

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

---

## 🔄 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) executes on pushes and pull requests:

1. **Backend CI**: Python setup, dependency installation, Ruff linting, MyPy type checking, and Pytest execution.
2. **Frontend CI**: Node.js setup, dependency installation, ESLint linting, TypeScript type checking, Vitest unit tests, and production build.
3. **Docker Smoke Test**: Multi-container Docker Compose build, service healthcheck polling, and API functionality verification.

---

## 🔧 Troubleshooting

### Database Migration Issues

If schema state gets out of sync during development:

```bash
cd backend
alembic stamp head
alembic check
```

### Docker Container Connection Issues

Ensure frontend connects to backend via container hostnames (`http://backend:8000`) within the Docker network, and check container logs:

```bash
docker compose logs backend
docker compose logs frontend
```
