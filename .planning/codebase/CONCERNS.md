# Codebase Concerns

**Analysis Date:** 2026-08-11

> This document reflects the **current, refactored** codebase (RAG package in `backend/services/rag/`, Alembic migrations, full test suite, CI, nginx proxy). Many issues present in earlier iterations (mock-fallback engine, hardcoded JWT default, passlib/bcrypt breakage, missing nginx proxy, memory-id collisions, zero tests, no migrations) have been resolved and are noted as such where relevant.

## Tech Debt

**Hardcoded production JWT secret in `docker-compose.yml`:**
- Issue: `docker-compose.yml` sets `JWT_SECRET_KEY=cozy_rag_productivity_tracker_super_secret_key_2026` for the production stack.
- Impact: Anyone with the repo can forge valid JWTs for any deployment that uses the compose defaults.
- Note: The application code itself has **no** hardcoded default (dev generates an ephemeral secret; production fails fast) — the risk is purely the compose file value.
- Fix approach: Remove the value from `docker-compose.yml`; require it from a `.env` file or secret store.

**`SEED_DEMO=true` in the production compose stack:**
- Issue: `docker-compose.yml` sets `SEED_DEMO=true` while also setting `APP_ENV=production`; the code gates demo seeding on `not settings.is_production` (`backend/main.py` lifespan), so it is currently inert — but the flag advertises intent and any misconfiguration (or removal of the guard) would seed the published `demo@cozy.app` / `cozy123` account into production.
- Impact: A known-credential backdoor account risk in any deployment that follows the compose example.
- Fix approach: Remove `SEED_DEMO` from the production compose file entirely.

**Frontend metric fallbacks fabricate data:**
- Issue: `frontend/src/App.tsx` renders `analytics?.current_streak_days || 4` and `analytics?.daily_completion || 1` in the header when analytics are null/loading.
- Impact: Users briefly see fabricated "4 Day Streak" / "1 completed today" instead of a placeholder.
- Fix approach: Render `0` or a skeleton/placeholder when `analytics` is null.

**Dual schema-management paths (dev `create_all` vs prod Alembic):**
- Issue: Dev lifespan calls `Base.metadata.create_all` (`backend/main.py`) while production relies on `alembic upgrade head`. `create_all` does not alter existing tables, so schema drift between dev DBs and the migration chain is possible.
- Fix approach: Use Alembic in dev too (or add a `check` in CI); keep `create_all` only as an explicit convenience.

**Frontend `AnalyticsDashboard` fetches its own analytics:**
- Issue: `App.tsx` already fetches analytics for the header, and `AnalyticsDashboard.tsx` fetches again on mount (`AnalyticsService.getAnalytics()`), duplicating requests; its `fetchAnalytics` has no `try/catch` (unhandled promise rejection on failure).
- Fix approach: Pass analytics down as props, or centralize fetch + error handling in `App.tsx`.

**Browser-native dialogs in `TaskManager.tsx`:**
- Issue: `handleComplete` uses `prompt()` and `handleDelete` uses `confirm()` (`frontend/src/components/TaskManager.tsx`).
- Impact: Inconsistent UX, blocked in some embedded contexts.
- Fix approach: Replace with the existing modal pattern.

**Unused RAG route parameter:**
- Issue: `get_user_rag_memories` in `backend/routes/rag_routes.py` accepts `db: Session = Depends(get_db)` but never uses it (`# noqa: F841`).
- Fix approach: Drop the parameter.

**Frontend/backend version drift:**
- Issue: `frontend/package.json` says `2.0.0` while backend `pyproject.toml`/`core/config.py` say `2.1.0`.
- Fix approach: Align versions (e.g., via a shared constant or a small release script).

## Known Bugs

**Potential silent ChromaDB → in-memory degradation (data loss):**
- Symptoms: If `chromadb` fails to initialize (missing dependency, corrupted store, disk error), `ChromaVectorStore` transparently switches to `InMemoryVectorStore` (`backend/services/rag/vector_store.py`). Memories appear saved but are volatile and vanish on restart; nothing in the UI/logs surfaces this mode.
- Files: `backend/services/rag/vector_store.py`
- Trigger: ChromaDB init failure at first use.
- Fix approach: Surface store status via `/health/ready` or logs; fail closed with a clear error or persist fallback to disk.

**Best-effort memory persistence can silently diverge from the DB:**
- Symptoms: `_persist_memory` in `backend/routes/task_routes.py` catches `MemoryIngestionError` and only logs it — task CRUD succeeds while the RAG memory is never stored.
- Impact: The AI assistant's memory of task events can be incomplete without the user knowing.
- Fix approach: Make memory writes transactional with the task write, or expose a consistency indicator/retry.

**Frontend `toLocaleDateString`/`toLocaleString` timezone rendering:**
- Symptoms: Task due dates and memory timestamps are ISO strings; rendering with `new Date(...).toLocaleDateString()` displays in the browser's local timezone while the backend stores UTC (`TaskManager.tsx`, `AIAssistant.tsx`).
- Impact: Off-by-one date display for users east/west of UTC.
- Fix approach: Format with explicit UTC (`toLocaleDateString(undefined, { timeZone: 'UTC' })`) or standardize display-timezone handling.

**`docker-smoke-test` completes task by hardcoded id:**
- Symptoms: CI `curl -X PUT "http://localhost:8000/api/tasks/1/complete..."` assumes task id 1, but the earlier `TASK_ID` extraction in `.github/workflows/ci.yml` is written but unused.
- Impact: Smoke test can fail on a non-empty database (id != 1).
- Fix approach: Parse and reuse the created task id in the complete step.

## Security Considerations

**Hardcoded secret in compose (see Tech Debt):**
- Risk: Token forgery in any compose-based deployment that doesn't override `JWT_SECRET_KEY`.
- Files: `docker-compose.yml`
- Recommendations: Externalize the secret; document a secret-generation step.

**No rate limiting on auth or LLM endpoints:**
- Risk: `/api/auth/login` and `/api/auth/register` (`backend/routes/auth_routes.py`) have no brute-force protection; `/api/rag/query` (`backend/routes/rag_routes.py`) lets an authenticated user choose free-form `provider` and `model_name` (`backend/schemas.py`), enabling LLM cost abuse (e.g., expensive model names) against paid keys.
- Files: `backend/routes/auth_routes.py`, `backend/routes/rag_routes.py`, `backend/services/rag/providers/registry.py`
- Current mitigation: Provider allowlist validation in the registry (unknown providers fall back to default) — but `model_name` is not allowlisted.
- Recommendations: Add rate limiting (slowapi / nginx `limit_req`); restrict `provider`/`model_name` to an allowlist; add per-user query budgets.

**JWT stored in localStorage:**
- Risk: `frontend/src/services/api.ts` stores the token in `localStorage`; any XSS can exfiltrate it. No httpOnly cookie alternative.
- Files: `frontend/src/services/api.ts`
- Current mitigation: React default escaping; no `dangerouslySetInnerHTML` found.
- Recommendations: Consider httpOnly cookies for production, or at minimum CSP headers on the served app.

**No server-side logout / token revocation:**
- Risk: Tokens are valid 7 days and cannot be invalidated server-side; frontend "logout" only removes `localStorage`.
- Files: `backend/routes/auth_routes.py`, `frontend/src/services/api.ts`
- Recommendations: Add a token denylist / refresh-token flow if revocation matters.

**Docker containers run as root:**
- Risk: `backend/Dockerfile` and `frontend/Dockerfile` produce root-run containers; a compromised app gets root in the container.
- Files: `backend/Dockerfile`, `frontend/Dockerfile`
- Recommendations: Add `USER` directives (e.g., `python:3.11-slim` → create non-root user; nginx image → `USER nginx`).

**CORS origins are fixed to localhost:**
- Risk: Low for current deployments, but `CORS_ORIGINS` defaults to `["http://localhost:3000", "http://localhost:5173"]`; if the frontend is ever served from another origin, requests fail or need config changes.
- Files: `backend/core/config.py`, `backend/main.py`
- Current mitigation: No wildcard; `allow_credentials=True` with explicit origins.

## Performance Bottlenecks

**Analytics computes everything in Python memory:**
- Problem: `get_analytics` fetches all tasks for the user and computes 11 metrics with list comprehensions (`backend/routes/analytics_routes.py`).
- Files: `backend/routes/analytics_routes.py`
- Cause: No SQL aggregation; `GET /api/tasks` also returns all rows with no pagination (`backend/routes/task_routes.py`).
- Improvement path: Push aggregation into SQL; paginate or cap the task list.

**Embedding model + retrieval cost on first RAG use:**
- Problem: `SentenceTransformer("all-MiniLM-L6-v2")` loads lazily on first use (~90MB+ model download on first run) and encodes on every store/query synchronously (`backend/services/rag/embeddings.py`).
- Files: `backend/services/rag/embeddings.py`, `backend/services/rag/vector_store.py`
- Improvement path: Preload/cache embeddings at startup; batch document embeddings (already done for documents); cache repeated queries.

**Startup seeding commits per row:**
- Problem: The seed loop in `backend/main.py` commits once per task and embeds/stores each memory separately — slow cold starts.
- Files: `backend/main.py`
- Improvement path: Single commit after batch; batch ChromaDB inserts.

**ChromaDB distance → score conversion:**
- Problem: Search converts distance to `1.0 - distance` (`backend/services/rag/vector_store.py`); scores across collections/models are not calibrated, and reranking recombines semantic/lexical/metadata/recency with fixed weights (`backend/services/rag/reranking.py`).
- Files: `backend/services/rag/vector_store.py`, `backend/services/rag/reranking.py`
- Improvement path: Use cosine similarity directly via `collection.query` with the configured distance function; validate weights against the evaluation dataset.

## Fragile Areas

**`backend/services/rag/vector_store.py` — silent store degradation:**
- Why fragile: ChromaDB init failure silently swaps in an in-memory store; `InMemoryVectorStore.search` is O(n) cosine against every record.
- Safe modification: Treat in-memory as an explicit degraded mode with a surfaced status; keep the `VectorStore` interface stable (tests depend on it).

**`backend/services/rag/pipeline.py` — LLM dependency on runtime config:**
- Why fragile: Provider/`model_name` come from request + settings at call time; a missing API key raises `LLMError` mid-request (gracefully handled, but the answer quality depends on provider availability).
- Safe modification: Keep the `LLMError` → graceful-answer path; consider a provider health check endpoint.

**Auth flow:**
- Files: `backend/routes/auth_routes.py`, `frontend/src/services/api.ts`
- Why fragile: No logout/revocation; 7-day tokens; localStorage-only session.
- Test coverage: Covered by `test_auth.py` and `test_security.py` (tamper/expiry/missing).

**Docker deployment:**
- Files: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`
- Why fragile: Hardcoded secret + `SEED_DEMO` in compose; root containers; SQLite-in-Docker is not used in prod (PostgreSQL is) but `DATABASE_URL` must be set correctly; Ollama reachability via `host.docker.internal` is host-dependent.

## Scaling Limits

**SQLite single-writer + embedded ChromaDB:**
- Current capacity: Single-process backend; SQLite with `check_same_thread: False` — fine for one user.
- Limit: Concurrent writes serialize; SQLite file locks across containers; ChromaDB `PersistentClient` is process-bound — unsafe across multiple uvicorn workers.
- Scaling path: PostgreSQL is already the production path (`DATABASE_URL`); for multi-worker, move ChromaDB to a server deployment and use per-user collections (already per-user: `user_{user_id}_memories`).

**In-memory fallback store:**
- Current capacity: `InMemoryVectorStore` grows unboundedly and is lost on restart whenever ChromaDB is unavailable.
- Scaling path: Fail closed with a clear error, or persist the fallback.

**Analytics computation:**
- Current capacity: O(n) full-table scan per request.
- Scaling path: SQL aggregation; materialized daily metric snapshots.

## Dependencies at Risk

**sentence-transformers / chromadb heavy installs:**
- Risk: Both are large native-backed packages; version pins are `~=` (`sentence-transformers~=3.0.0`, `chromadb~=0.5.0`) so major/minor bumps stay within ranges, but ChromaDB 0.5 → 0.6/1.x API drift is a real future risk.
- Migration plan: Isolate behind the existing `VectorStore`/`EmbeddingService` abstractions (already in place); update pins deliberately and run the offline test suite.

**bcrypt / PyJWT are current and maintained** — the earlier passlib + python-jose risk is resolved.

**ollama local model availability:**
- Risk: Default `RAG_PROVIDER=ollama` with model `llama3` assumes a local Ollama; without it, RAG queries return the graceful "unavailable" answer.
- Migration plan: Document provider setup; the provider registry already allows `openai`/`gemini`/`grok` via keys.

## Missing Critical Features

**Server-side logout / token revocation:**
- Problem: No `/logout` or token invalidation; tokens live 7 days.
- Blocks: Security-sensitive deployments; shared/compromised device scenarios.

**Rate limiting:**
- Problem: No throttling on auth or LLM endpoints (see Security).
- Blocks: Public-facing deployments.

**Observability:**
- Problem: Stdlib logging + request middleware exist, but no structured logging, metrics, or error tracking; `/health/ready` only checks the database.
- Blocks: Production debugging; incident response; capacity planning.

**Password management:**
- Problem: No change-password, reset, or email verification.
- Blocks: Basic account lifecycle requirements.

**Frontend component test coverage for the remaining UI:**
- Problem: Only `AIAssistant` and the API service layer have frontend tests; `TaskManager`, `AuthModal`, `AnalyticsDashboard`, `CuteHeader`, and `App` are untested.
- Blocks: Confident refactoring of the task/auth/analytics UI.

## Test Coverage Gaps

**Well covered:** Backend auth (register/login/me/token edge cases), task CRUD + cross-user isolation, analytics metrics (incl. empty user), health endpoints, RAG pipeline (retrieval, rerank, grounding, context, injection defense, benchmark), security regressions (JWT tamper/expiry, cross-user memory, oversized input, prod secret validation), and the frontend RAG assistant + API service layer.

**Gaps:**
- Frontend: no tests for `TaskManager.tsx` (CRUD flows, filters, modals, `prompt`/`confirm`), `AuthModal.tsx` (login/register/toggle/error display), `AnalyticsDashboard.tsx` (loading, charts, empty data), `CuteHeader.tsx`, or `App.tsx` (tab switching, 401 handler, logout).
- No coverage gate in CI (backend and frontend both have coverage tooling available).
- No E2E suite (only the CI Docker smoke test).
- RAG benchmark runs on fakes only — no test with real embeddings/ChromaDB semantics (acceptable for CI determinism, but worth a nightly tagged run).

---

*Concerns audit: 2026-08-11*
