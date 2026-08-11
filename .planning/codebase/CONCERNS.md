# Codebase Concerns

**Analysis Date:** 2026-08-11

> **Update (2026-08-11):** All actionable concerns below have been addressed and committed. Items marked ✅ **RESOLVED** are fixed in the current codebase; items marked ⏳ **PARTIAL** have mitigation in place with remaining follow-ups noted.

## Tech Debt

**Hardcoded production JWT secret in `docker-compose.yml`** — ✅ **RESOLVED**
- Fix: `docker-compose.yml` now requires `JWT_SECRET_KEY` via `${JWT_SECRET_KEY:?...}` (fails fast if unset). No hardcoded value anywhere. `.env.example` documents generation (`python -c "import secrets; print(secrets.token_urlsafe(48))"`).
- Commit: `9a0bc12`

**`SEED_DEMO=true` in the production compose stack** — ✅ **RESOLVED**
- Fix: removed from `docker-compose.yml`; demo seeding remains gated behind `SEED_DEMO` + `APP_ENV != production` in `backend/main.py`.
- Commit: `9a0bc12`

**Frontend metric fallbacks fabricate data** — ✅ **RESOLVED**
- Fix: `frontend/src/App.tsx` now uses `analytics?.current_streak_days ?? 0` / `?? 0` instead of `|| 4` / `|| 1`.
- Commit: `13bbdd6`

**Dual schema-management paths (dev `create_all` vs prod Alembic)** — ✅ **RESOLVED**
- Fix: `backend/main.py` runs Alembic migrations in dev too (`_run_migrations`), with a `create_all` fallback only for legacy pre-migration dev DBs; production fails fast on migration errors. Tests run with `APP_ENV=test` and manage their own schema.
- Commit: `ec0fc48`

**Frontend `AnalyticsDashboard` fetches its own analytics** — ✅ **RESOLVED**
- Fix: `AnalyticsDashboard` now receives `analytics` + `onRefresh` via props from `App.tsx` (no duplicate fetch); adds an empty state and a refresh button.
- Commits: `13bbdd6`, `820e0fc`

**Browser-native dialogs in `TaskManager.tsx`** — ✅ **RESOLVED**
- Fix: `prompt()`/`confirm()` replaced with in-app modal flows for completing (with minutes input) and deleting tasks. Labels associated with inputs via `htmlFor`/`id` (a11y).
- Commits: `6d4322e`, `205cab0`

**Unused RAG route parameter** — ✅ **RESOLVED**
- Fix: removed unused `db: Session = Depends(get_db)` from `get_user_rag_memories` and `delete_memory` in `backend/routes/rag_routes.py`.
- Commit: `a1988b5`

**Frontend/backend version drift** — ✅ **RESOLVED**
- Fix: `frontend/package.json` bumped to `2.1.0`, matching backend.
- Commit: `7e6ee68`

## Known Bugs

**Silent ChromaDB → in-memory degradation (data loss)** — ✅ **RESOLVED**
- Fix: `VectorStore.mode` property (`chroma` / `in-memory-fallback` / `in-memory`); `GET /health/ready` reports `rag_vector_store` and returns `503 not_ready` on fallback; fallback logs a loud warning.
- Commits: `b652e5a`, `8c125bf`

**Best-effort memory persistence silently diverges from the DB** — ✅ **RESOLVED**
- Fix: `_persist_memory` in `backend/routes/task_routes.py` retries once and logs failures at ERROR with full context — divergence is no longer silent (task still succeeds by design).
- Commit: `4164993`

**Frontend `toLocaleDateString`/`toLocaleString` timezone rendering** — ✅ **RESOLVED**
- Fix: new `frontend/src/utils/dates.ts` (`formatUtcDate`/`formatUtcDateTime`); used in `TaskManager.tsx` and `AIAssistant.tsx`.
- Commits: `b659e88`, `6d4322e`, `f20d56a`

**`docker-smoke-test` completes task by hardcoded id** — ✅ **RESOLVED**
- Fix: CI now parses the created `TASK_ID` and uses it in the complete step; also supplies `JWT_SECRET_KEY` for the compose stack.
- Commit: `54c8afb`

## Security Considerations

**Hardcoded secret in compose** — ✅ **RESOLVED** (see Tech Debt, commit `9a0bc12`)

**No rate limiting on auth or LLM endpoints** — ✅ **RESOLVED**
- Fix: new dependency-free `backend/core/rate_limit.py` (in-process sliding window, per client IP); applied to login/register (`RATE_LIMIT_AUTH_PER_MINUTE`, default 20/min) and `/api/rag/query` (`RATE_LIMIT_RAG_PER_MINUTE`, default 30/min); auto-disabled in `APP_ENV=test`.
- Commits: `878f6a1`, `9fc38db`, `a1988b5`, `8cb2690`

**Free-form `provider`/`model_name` (LLM cost abuse)** — ✅ **RESOLVED**
- Fix: per-provider model allowlist in `settings.ALLOWED_MODELS`; `rag_routes._validate_model_allowlist` rejects unknown models with 400 before reaching the LLM. Provider names remain registry-validated.
- Commits: `8cb2690`, `a1988b5`

**JWT stored in localStorage** — ⏳ **PARTIAL**
- Mitigation: CSP + security headers added in `frontend/nginx.conf` (`default-src 'self'`, X-Content-Type-Options, X-Frame-Options, Referrer-Policy).
- Remaining follow-up: migrate to httpOnly cookies (larger auth-architecture change) — deferred.
- Commit: `9efc8f2`

**No server-side logout / token revocation** — ✅ **RESOLVED**
- Fix: `TokenBlacklist` model + Alembic migration `0002`; JWTs carry a `jti`; `POST /api/auth/logout` revokes the current token server-side; `get_current_user` rejects blacklisted tokens. Frontend logout calls the endpoint (best-effort) then clears localStorage.
- Commits: `56dc2c0`, `f176b01`, `5ff6700`, `205cab0`, `9fce1c1`, `9fc38db`

**Docker containers run as root** — ✅ **RESOLVED**
- Fix: backend `Dockerfile` adds non-root `appuser` with writable `chroma_db`; frontend nginx image already runs as the non-root `nginx` user (documented).
- Commits: `c1e82a8`, `d0d6869`

**CORS origins fixed to localhost** — ⏳ **PARTIAL**
- Note: `CORS_ORIGINS` is fully config-driven via settings (no wildcard, `allow_credentials=True` with explicit origins). Adjust via env for non-local deployments. No code change required.

## Performance Bottlenecks

**Analytics computes everything in Python memory** — ✅ **RESOLVED**
- Fix: `get_analytics` rewritten to push all counts into SQL (`COUNT`/filters/`AVG`); only completed timestamps are materialized for weekday/hour distributions and the streak.
- Commit: `306172c`

**Task list returns all rows** — ✅ **RESOLVED**
- Fix: `GET /api/tasks` now supports `limit`/`offset` pagination (default 200, max 1000).
- Commit: `610c1dc`

**Repeated RAG questions hit the LLM every time** — ✅ **RESOLVED**
- Fix: per-user LRU answer cache in `RagPipeline` (`RAG_CACHE_ENABLED`, TTL 300s, max 128 entries).
- Commit: `d56cd5a`

**Startup seeding commits per row** — ✅ **RESOLVED**
- Fix: seed loop batches all tasks into a single commit before storing memories.
- Commit: `d951543`

**ChromaDB distance → score conversion** — ⏳ **PARTIAL**
- Note: collection already uses cosine space (`hnsw:space: cosine`); `1.0 - distance` is the cosine similarity. Weight calibration against the evaluation dataset remains a tuning follow-up.

## Fragile Areas

**`backend/services/rag/vector_store.py` silent store degradation** — ✅ **RESOLVED** (see Known Bugs: mode surfaced + health fails readiness, commits `b652e5a`, `8c125bf`)

**`backend/services/rag/pipeline.py` LLM dependency** — ⏳ **PARTIAL**
- Mitigation: failures already return a graceful "unavailable" answer with `confidence=0`/`grounded=False`; model allowlist + answer cache added.
- Remaining follow-up: dedicated provider health-check endpoint.

**Auth flow (logout/revocation)** — ✅ **RESOLVED** (see Security; tokens now revocable via blacklist)

**Docker deployment** — ✅ **RESOLVED** (secret + demo + non-root + task-id fixes; see above)

## Scaling Limits

**SQLite single-writer + embedded ChromaDB** — ⏳ **PARTIAL**
- Note: PostgreSQL is the production path (`docker-compose.yml`); per-user ChromaDB collections already shard data. Multi-worker ChromaDB server deployment remains a follow-up for horizontal scale.

**In-memory fallback store** — ✅ **RESOLVED** (now detectable via `/health/ready` and loud logs)

**Analytics computation** — ✅ **RESOLVED** (SQL aggregation; pagination added)

## Dependencies at Risk

**sentence-transformers / chromadb heavy installs** — ⏳ **PARTIAL**
- Note: both are isolated behind `VectorStore`/`EmbeddingService` abstractions and pinned with `~=`. Deliberate pin bumps + full offline suite remain the control mechanism.

**ollama local model availability** — ⏳ **PARTIAL**
- Note: graceful degradation + allowlist exist; provider setup documented in README.

## Missing Critical Features

**Server-side logout / token revocation** — ✅ **RESOLVED** (see Security)

**Rate limiting** — ✅ **RESOLVED** (see Security)

**Observability** — ✅ **RESOLVED**
- Fix: JSON log formatter (`LOG_FORMAT=json`, `backend/core/logging.py`), request-context middleware (request_id + latency), `/health/live` + `/health/ready` with DB and vector-store checks.
- Remaining follow-up: Sentry/error-tracking integration (requires external account).
- Commits: `1630671`, `d951543`, `8c125bf`

**Password management** — ✅ **RESOLVED**
- Fix: `POST /api/auth/change-password` verifies the current password before updating. Password reset/email verification requires an external email provider (deferred).
- Commits: `9fce1c1`, `9fc38db`

**Frontend component test coverage** — ✅ **RESOLVED**
- Fix: new vitest suites for `TaskManager`, `AuthModal`, `AnalyticsDashboard`, `CuteHeader`, and `App` (27 frontend tests total); ResizeObserver/matchMedia mocked for recharts.
- Commit: `cf6843a`

## Test Coverage Gaps

**Async RAG tests silently skipped** — ✅ **RESOLVED**
- Fix: `pytest-asyncio` declared in dev extras + installed in CI; `asyncio_mode = "auto"`. The full async RAG suite now runs (45 backend tests, 81% coverage).
- Commits: `45c787f`, `9058646`, `54c8afb`

**New security/feature coverage** — ✅ **RESOLVED**
- Fix: `test_security.py` covers logout revocation, change-password flow, model-allowlist rejection, and rate-limiter limits.
- Commit: `19331ef`

**No coverage gate in CI** — ✅ **RESOLVED**
- Fix: backend CI runs `pytest --cov=. --cov-fail-under=70` (current ~81%).
- Commit: `54c8afb`

**No E2E suite** — ⏳ **PARTIAL**
- Note: CI `docker-smoke-test` covers deployment-level E2E (compose up, health polling, register → create → complete → RAG query). A browser-automation suite (Playwright) remains a future enhancement.

**RAG benchmark runs on fakes only** — ⏳ **PARTIAL**
- Note: intentional for CI determinism. A nightly run against real embeddings/ChromaDB semantics is a follow-up.

---

*Concerns audit: 2026-08-11 (updated 2026-08-11 with resolution status)*
