# Codebase Concerns

**Analysis Date:** 2026-08-11

## Tech Debt

**Frontend mock-fallback engine (`frontend/src/services/api.ts`):**
- Issue: Every API service method (`AuthService`, `TaskService`, `AnalyticsService`, `RAGService`) wraps real HTTP calls in `try/catch` and silently returns hardcoded mock data on ANY error (`api.ts:96-105`, `api.ts:113-118`, `api.ts:141-142`, `api.ts:149-171`, `api.ts:179-182`, `api.ts:190-204`, `api.ts:212-223`, `api.ts:233-249`, `api.ts:260-282`). Authentication failures become "successful" local logins with a fake `mock_token_123` (`api.ts:103`, `api.ts:116`).
- Impact: Users are shown fabricated data, real backend errors (401/500) are invisible, local edits diverge from server state, and "logged-in" users may have no valid session. The error branch in `frontend/src/components/AuthModal.tsx:37` is effectively unreachable.
- Fix approach: Remove mock fallbacks from production services; let errors propagate so `AuthModal` and components can display them. Keep mocks only behind an explicit dev flag (e.g., `import.meta.env.DEV && VITE_USE_MOCK`).

**No database migrations:**
- Issue: Schema is created with `Base.metadata.create_all(bind=engine)` at import time (`backend/main.py:11`, `backend/database.py:12-15`). No Alembic or any migration tooling exists.
- Impact: Adding/renaming columns requires manual DB deletion; existing deployments cannot upgrade; schema drift between environments is guaranteed.
- Fix approach: Introduce Alembic with an initial migration matching `backend/models.py`, wire it into startup/Docker entrypoint.

**Broken frontend quality gates:**
- Issue: `frontend/package.json:9` declares `"lint": "eslint . --ext ts,tsx..."` but `eslint` is not in `devDependencies` and there is no `.eslintrc*` or `eslint.config.*` file anywhere in the repo. `npm run lint` fails immediately.
- Impact: No linting runs; dead script misleads developers.
- Fix approach: Add `eslint` + `typescript-eslint` and a config file, or remove the script.

**Deprecated APIs in use:**
- `@app.on_event("startup")` deprecated in FastAPI (`backend/main.py:34`) — use lifespan context manager.
- `task_in.dict(exclude_unset=True)` deprecated in Pydantic v2 (`backend/routes/task_routes.py:74`) — use `model_dump(exclude_unset=True)`.
- `datetime.utcnow()` deprecated in Python 3.12 (`backend/main.py:50`, `backend/auth.py:28,30`, `backend/routes/task_routes.py:85,127,159`, `backend/routes/analytics_routes.py:18`, `backend/rag_service.py:67,109,132`) — use `datetime.now(timezone.utc)`.
- Impact: Deprecation warnings, eventual breakage on Python 3.13+/FastAPI updates.

**Unbounded dependency pins (`backend/requirements.txt`):**
- Issue: All pins are bare lower bounds (`fastapi>=0.100.0`, `sqlalchemy>=2.0.0`, `pydantic>=2.0.0`, `chromadb>=0.4.0`, `sentence-transformers>=2.2.2`).
- Impact: Non-reproducible installs; a future major release can break the app (e.g., chromadb 0.4 → 1.x API drift, pydantic 2 → 3).
- Fix approach: Pin exact versions (or `~=`) and commit a lockfile (`pip freeze` / uv lock). Use `npm ci` with the existing `frontend/package-lock.json` instead of `npm install` (`frontend/Dockerfile:6`).

**Hardcoded credentials and secrets in repo:**
- Issue: Default JWT secret `cozy_rag_productivity_tracker_super_secret_key_2026` is in `backend/auth.py:12`, `README.md:84`, and `docker-compose.yml:12`. Demo account `demo@cozy.app` / `cozy123` is seeded in `backend/main.py:38-44`. No `.env.example` exists.
- Impact: Anyone with the repo can forge JWTs and log into the seeded demo account (published default credentials).
- Fix approach: Require `JWT_SECRET_KEY` from env with no default in non-dev; generate a random secret; remove demo seeding behind a `SEED_DEMO` flag; document vars in `.env.example`.

**RAG memory generation duplicated across layers:**
- Issue: Memory strings are generated inline in seeding (`backend/main.py:109-127`), task routes (`backend/routes/task_routes.py:49-56, 90-111, 134-140, 158-161`), and frontend mock code (`frontend/src/services/api.ts:163-169, 197-203, 215-221`). The same "completed X in Y minutes" phrasing exists in 3 places.
- Impact: Inconsistent memory quality; changes must be made in multiple files.
- Fix approach: Keep all memory synthesis in `backend/rag_service.py` helpers; call them from routes only.

**Frontend Docker image missing API proxy:**
- Issue: `frontend/Dockerfile:11-13` serves static files via default nginx with no `nginx.conf`; `frontend/src/services/api.ts:4` calls relative `/api`, which nginx has no route for.
- Impact: The Docker Compose deployment (`docker-compose.yml`) serves a UI whose API calls all 404 — the app is non-functional in the advertised one-command deployment.
- Fix approach: Add an nginx config that proxies `/api` → `backend:8000` and copy it in `frontend/Dockerfile`.

## Known Bugs

**Docker deployment cannot reach the backend:**
- Symptoms: `docker-compose up --build` starts both services; browser UI loads but every request to `/api/*` returns nginx 404.
- Files: `frontend/Dockerfile`, `frontend/src/services/api.ts:4`, `docker-compose.yml:21-28`
- Trigger: Any interaction (login, task CRUD, analytics) in the Docker-served UI.
- Workaround: Run locally with the Vite dev proxy (`frontend/vite.config.ts:9-14`) or reverse-proxy manually.

**Incorrect credentials appear to log in successfully:**
- Symptoms: Any email/password "logs in"; the auth modal closes and shows a fake user; the wrong-password error message (`frontend/src/components/AuthModal.tsx:37`) never displays.
- Files: `frontend/src/services/api.ts:108-119` (login catch), `api.ts:94-106` (register catch), `api.ts:121-128` (getCurrentUser catch)
- Trigger: Submit login with a non-existent account or wrong password while backend is running or down.
- Workaround: None from the UI — the app believes you are authenticated.

**Memory ID collisions in ChromaDB:**
- Symptoms: Two memories stored in the same millisecond get the same id `mem_u{user_id}_{int(time.time()*1000)}` (`backend/rag_service.py:104`); ChromaDB `collection.add` (line 116) rejects duplicate ids, memory silently dropped.
- Files: `backend/rag_service.py:104-134`
- Trigger: Scripted/batched inserts (e.g., seeding loop `backend/main.py:102-127`, rapid create+update).
- Fix approach: Use `uuid4` or include a monotonic counter/random suffix.

**passlib + bcrypt 4.x incompatibility:**
- Symptoms: `AttributeError: module 'bcrypt' has no attribute '__about__'` on login/register; server 500s.
- Files: `backend/requirements.txt:6` (`passlib[bcrypt]>=1.7.4` pulls latest bcrypt), `backend/auth.py:16`
- Trigger: Fresh `pip install` today (bcrypt >= 4.1). passlib 1.7.4 is unmaintained and breaks with bcrypt >= 4.1.
- Workaround: Pin `bcrypt==4.0.1`.
- Fix approach: Replace passlib with `bcrypt` directly (`bcrypt.hashpw`/`checkpw`) or move to `pwdlib`.

**Hardcoded streak/analytics fallback values:**
- Symptoms: Logged-out users and failed fetches show "4 Day Streak" and "1 completed today" fabricated by `frontend/src/App.tsx:48-49` (`analytics?.current_streak_days || 4`, `analytics?.daily_completion || 1`).
- Files: `frontend/src/App.tsx:48-49`
- Trigger: Load app without a backend or after logout (`handleLogout` calls `reloadData()` at `App.tsx:38`, which falls into mocks).
- Fix approach: Render `0`/placeholder when no data; don't substitute fake metrics.

**Naive vs aware datetime mixing:**
- Symptoms: Frontend sends `new Date(...).toISOString()` (UTC with `Z`, e.g., `TaskManager.tsx:57,67`) while backend compares with naive `datetime.utcnow()` (`backend/routes/analytics_routes.py:18`, `backend/routes/task_routes.py:85`). Due dates may parse inconsistently through SQLAlchemy/SQLite; overdue and delay logic can misbehave.
- Files: `backend/routes/task_routes.py:71-97`, `backend/routes/analytics_routes.py:18-56`, `frontend/src/components/TaskManager.tsx:42,57,67`
- Fix approach: Standardize on timezone-aware UTC datetimes end-to-end; serialize/parse explicitly.

**`/api/rag/memories` retrieves with a fixed generic query:**
- Symptoms: Memory list may omit relevant entries because retrieval is semantic against the fixed string "task productivity activity completed created delayed" with `top_k=20` (`backend/routes/rag_routes.py:35`), not an exhaustive listing.
- Files: `backend/routes/rag_routes.py:30-36`
- Fix approach: Read the user's collection documents/metadatas directly (with pagination) instead of a semantic query.

## Security Considerations

**Hardcoded JWT secret enables token forgery:**
- Risk: `backend/auth.py:12` defaults to a public secret; same secret hardcoded in `docker-compose.yml:12` and documented in `README.md:84`. Any attacker can sign arbitrary `sub` claims and impersonate any user.
- Files: `backend/auth.py:12`, `docker-compose.yml:12`, `README.md:84`
- Current mitigation: None (secret only "protected" by env override).
- Recommendations: Remove default secret; fail startup if `JWT_SECRET_KEY` unset in production; generate per-deployment secret.

**CORS wildcard with credentials:**
- Risk: `allow_origins=["*"]` + `allow_credentials=True` (`backend/main.py:20-26`) is both invalid (browsers reject credentialed wildcard responses) and an open-door policy if cookies are ever used.
- Files: `backend/main.py:20-26`
- Current mitigation: Frontend uses bearer tokens, not cookies.
- Recommendations: Restrict `allow_origins` to the frontend origin (e.g., `http://localhost:3000`) or drop `allow_credentials`.

**No rate limiting on auth or LLM endpoints:**
- Risk: `/api/auth/login` and `/api/auth/register` (`backend/routes/auth_routes.py`) have no brute-force protection. `/api/rag/query` (`backend/routes/rag_routes.py:12`) lets any authenticated user choose `provider` and free-form `model_name` (`backend/rag_service.py:243,267,282,303`), enabling LLM cost abuse (e.g., expensive model names) with paid API keys.
- Files: `backend/routes/auth_routes.py`, `backend/routes/rag_routes.py`, `backend/schemas.py:78-81`
- Current mitigation: None.
- Recommendations: Add rate limiting (slowapi / nginx limit_req); restrict `provider`/`model_name` to an allowlist; add per-user query budgets.

**Prompt injection via questions and stored memories:**
- Risk: The user's question and stored memory text (derived from user-entered task titles/descriptions, `backend/routes/task_routes.py:50-56`) are concatenated directly into the LLM system prompt (`backend/rag_service.py:228-236, 245-247`). A crafted task title like "ignore the instructions above" becomes an injected directive.
- Files: `backend/rag_service.py:228-236`
- Current mitigation: System prompt admonition only ("MUST base answers strictly on...") — trivially overridable.
- Recommendations: Separate untrusted content with delimiters, filter instructions, or use a non-instructional framing; consider sanitizing stored task text.

**API key exposure in URL:**
- Risk: Gemini key passed as URL query parameter (`https://generativelanguage.googleapis.com/...?key={api_key}`) in `backend/rag_service.py:282` — keys in URLs leak into access logs/proxies.
- Files: `backend/rag_service.py:282`
- Current mitigation: Server-side only (keys read from env at `rag_service.py:257,279,296`; never in frontend — verified `frontend/src/` has no key literals).
- Recommendations: Use the `x-goog-api-key` header instead of query param.

**JWT stored in localStorage:**
- Risk: `frontend/src/services/api.ts:14-18, 98, 111` reads/stores the token in `localStorage`; any XSS can exfiltrate it. No httpOnly cookie alternative.
- Files: `frontend/src/services/api.ts:14-18`
- Current mitigation: React default escaping (no `dangerouslySetInnerHTML` found).
- Recommendations: Consider httpOnly cookies for production, or at minimum CSP headers on the served app.

**Published default demo account:**
- Risk: `demo@cozy.app` / `cozy123` seeded on every fresh start (`backend/main.py:38-44`), with credentials printed in the README setup flow (`README.md:51`). This is a known backdoor account in any deployment.
- Files: `backend/main.py:38-44`
- Recommendations: Gate demo seeding behind an env flag; remove default password from docs.

**Docker containers run as root:**
- Risk: `backend/Dockerfile:1` and `frontend/Dockerfile:1,11` produce root-run containers; a compromised app gets root in the container.
- Files: `backend/Dockerfile`, `frontend/Dockerfile`
- Recommendations: Add `USER node` / non-root user in both images.

## Performance Bottlenecks

**Analytics loads the entire task table into Python memory:**
- Problem: `get_analytics` fetches all tasks for the user then computes 11 metrics with list comprehensions (`backend/routes/analytics_routes.py:17-80`).
- Files: `backend/routes/analytics_routes.py:17-80`
- Cause: No SQL aggregation; `GET /api/tasks` also returns all rows with no pagination (`backend/routes/task_routes.py:13-27`).
- Improvement path: Push aggregation into SQL (`COUNT`/`GROUP BY` on status, date ranges, `AVG(actual_minutes)`); paginate or cap the task list.

**Synchronous embedding + LLM calls inside request handlers:**
- Problem: `SentenceTransformer("all-MiniLM-L6-v2")` loads at import (`backend/rag_service.py:42`, ~90MB+ model download on first run); every `/api/rag/query` synchronously encodes the query and blocks for upstream LLM calls with 5-10s timeouts (`backend/rag_service.py:249,271,291,310`).
- Files: `backend/rag_service.py:42, 145-170, 241-314`
- Cause: Single uvicorn worker (`backend/Dockerfile:18`) + blocking HTTP calls.
- Improvement path: Run LLM calls in a thread pool (`run_in_executor`), preload/cache embeddings, add response caching for repeated questions, and increase workers only if SQLite concurrency is addressed.

**Startup seeding commits per row:**
- Problem: Seed loop commits once per task inside the loop (`backend/main.py:102-117`), each also triggering a ChromaDB embed+store — slow cold starts.
- Files: `backend/main.py:102-127`
- Improvement path: Single commit after batch; batch ChromaDB inserts.

**ChromaDB distance→score conversion:**
- Problem: Retrieval converts distance to a pseudo-probability `1.0 - distance` (`backend/rag_service.py:162-168`) — the same distance from different collections/models is not calibrated across users; Evaluator then adds a flat `+0.2` bias (`backend/rag_service.py:209`).
- Files: `backend/rag_service.py:162-168, 208-210`
- Improvement path: Use cosine similarity directly via `collection.query` with appropriate `distance_function`; calibrate thresholds.

## Fragile Areas

**`backend/rag_service.py` — silent multi-level degradation:**
- Files: `backend/rag_service.py:35-50, 112-134, 147-189`
- Why fragile: ChromaDB/embedding import failure silently switches to a module-level in-memory list (`in_memory_docs`, line 50) that is lost on restart and never persisted. Per-store errors are caught and logged (`store_memory`, lines 123-124) with the caller unaware that the memory was not persisted. If the SentenceTransformer model can't download (offline), every memory silently goes to volatile memory.
- Safe modification: Treat in-memory fallback as a degraded mode with explicit log-to-console + surface status via an endpoint; never silently drop writes; make memory writes transactional with the task write.

**`frontend/src/services/api.ts` mock engine:**
- Files: `frontend/src/services/api.ts`
- Why fragile: Every service has dual code paths (real + mock); state lives in mutable module globals (`mockTasks`, `mockMemories`); behavior differs between dev and deploy. Any refactor of the API contract must be done twice.
- Safe modification: Extract mocks to `src/mocks/` behind a single `isMockMode()` gate before touching services.

**Auth flow:**
- Files: `backend/routes/auth_routes.py`, `frontend/src/services/api.ts:94-133`
- Why fragile: No logout/revocation endpoint (tokens valid 7 days, `backend/auth.py:14`); no refresh tokens; frontend "logout" is localStorage removal only (`api.ts:130-132`); server has no way to invalidate a stolen token.
- Test coverage: None.

**Docker deployment:**
- Files: `docker-compose.yml`, `frontend/Dockerfile`, `backend/Dockerfile`
- Why fragile: Broken `/api` proxying (see Known Bugs); SQLite file + ChromaDB volume mounted from host (`docker-compose.yml:15-16`) — multi-instance or concurrent host access corrupts SQLite; no healthchecks; `restart: always` with no readiness.

## Scaling Limits

**SQLite single-writer + embedded ChromaDB:**
- Current capacity: Single-process backend, SQLite with `check_same_thread: False` (`backend/database.py:10`) — fine for one user.
- Limit: Concurrent writes serialize; SQLite file locked across containers; ChromaDB `PersistentClient` (`backend/rag_service.py:41`) is process-bound — the volume mount in Docker is shared but the client state is not safe across multiple uvicorn workers.
- Scaling path: Move to PostgreSQL (`DATABASE_URL` already supported, `backend/database.py:7`) and a separate ChromaDB server deployment; add per-user collection sharding (already per-user collection naming at `backend/rag_service.py:114`).

**In-memory fallback store:**
- Current capacity: `in_memory_docs` grows unboundedly (`backend/rag_service.py:50, 127-133`) whenever ChromaDB is unavailable.
- Limit: Memory exhaustion on long-running degraded deployments; total data loss on restart.
- Scaling path: Persist fallback to SQLite/JSON file; or fail closed with a clear error.

**Analytics computation:**
- Current capacity: O(n) full-table scan per request (`backend/routes/analytics_routes.py:17`).
- Limit: Latency grows linearly with task count; metric computation repeated on every dashboard load.
- Scaling path: SQL aggregation; materialized daily metric snapshots.

## Dependencies at Risk

**passlib 1.7.4 (with bcrypt):**
- Risk: Unmaintained since 2020; breaks with bcrypt >= 4.1 (see Known Bugs).
- Impact: Auth is the first thing to break on fresh installs; silently leaves users locked out with 500s.
- Migration plan: Use `bcrypt` directly or `pwdlib`; hash-and-verify-only API in `backend/auth.py:16-23` makes this a contained change.

**python-jose[cryptography]:**
- Risk: `python-jose` is effectively unmaintained (last release 3.3.0, 2021); `pyjwt` is the maintained alternative.
- Impact: JWT handling is security-critical; stale crypto deps risk unpatched CVEs.
- Migration plan: Swap to `PyJWT` in `backend/auth.py:4,32,42` (API is nearly identical).

**chromadb / sentence-transformers unbounded:**
- Risk: `chromadb>=0.4.0` and `sentence-transformers>=2.2.2` with no upper bounds (`backend/requirements.txt:8-9`); ChromaDB 0.4 → 1.x changed client API significantly.
- Impact: A future `pip install` can break `PersistentClient`/`get_or_create_collection` usage.
- Migration plan: Pin versions verified against `backend/rag_service.py` API usage; isolate behind a thin vector-store adapter.

**Unpinned fastapi/pydantic:**
- Risk: `fastapi>=0.100.0`, `pydantic>=2.0.0` — major bumps remove deprecated APIs this code relies on (`on_event`, `.dict()`).
- Impact: Silent breakage on dependency updates.
- Migration plan: Pin `~=` and update code for modern APIs (lifespan, `model_dump`).

## Missing Critical Features

**Server-side logout / token revocation:**
- Problem: `backend/routes/auth_routes.py` has no `/logout`; tokens live 7 days (`backend/auth.py:14`) and cannot be invalidated. Compromised tokens persist until expiry.
- Blocks: Any security-sensitive deployment; shared/compromised device scenarios.

**Input enum validation:**
- Problem: `priority`/`status` are free strings in `backend/schemas.py:33-34`; backend uppercases but never validates (`backend/routes/task_routes.py:39-40, 76-79`). Invalid statuses silently enter the DB and skew analytics (only `PENDING`/`IN_PROGRESS` count as pending at `backend/routes/analytics_routes.py:25`).
- Blocks: Data integrity; analytics accuracy.

**Migrations (see Tech Debt):**
- Problem: No Alembic; `create_all` only.
- Blocks: Schema evolution, safe production upgrades.

**Password management:**
- Problem: No change-password, reset, or email verification. `UserCreate.password` min length 6 (`backend/schemas.py:9`).
- Blocks: Basic account lifecycle requirements.

**Observability:**
- Problem: No structured logging setup; scattered `print(f"Startup seeding error: {e}")` (`backend/main.py:131`) and module-level `logger` with no config (`backend/rag_service.py:32`). No request logging, error tracking, or health endpoint beyond the static `/` (`backend/main.py:135-143`).
- Blocks: Production debugging; incident response.

## Test Coverage Gaps

**Zero tests anywhere:**
- What's not tested: All of it. No `*.test.*`/`*.spec.*` files, no `pytest.ini`, no vitest/jest config. `pytest>=7.4.0` is declared in `backend/requirements.txt:11` but unused.
- Files: `backend/` (all), `frontend/src/` (all)
- Risk: The RAG pipeline math (`backend/rag_service.py:162-168, 208-210`), analytics metrics (`backend/routes/analytics_routes.py`), auth/JWT behavior, and the entire frontend mock-fallback behavior are unverifiable; regressions ship silently.
- Priority: High — especially `backend/auth.py` (security), `backend/rag_service.py` (algorithmic scoring), and `backend/routes/analytics_routes.py` (11 metrics with edge cases like empty sets, division by zero).

**Untested critical paths:**
- What's not tested: Register/login flow, JWT expiry/forgery resistance, task update → RAG memory generation (delay/complete branches in `backend/routes/task_routes.py:90-111`), ChromaDB failure fallbacks, Docker compose startup.
- Files: `backend/routes/auth_routes.py`, `backend/routes/task_routes.py`, `backend/routes/rag_routes.py`, `docker-compose.yml`
- Risk: The bug classes listed above (bcrypt crash, memory-id collision, missing nginx proxy) would all have been caught by basic smoke tests.
- Priority: High

---

*Concerns audit: 2026-08-11*
