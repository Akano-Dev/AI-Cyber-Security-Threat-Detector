# ACSTD Revamp — Working Reference

> Compact mirror of `PROJECT_PLAN.txt`. Used to reload context cheaply.
> **Current status:** Phase 1 backend DONE + 9 tests green. Frontend wiring + README + live-server check remain. See "Resume here" at bottom.

> **Plan adjustment (P1):** DB stays a repository over sqlite3 for now; SQLAlchemy + Postgres moved to **P5** (less risk, same abstraction). Recorded intentionally.

## Locked decisions
- **Deliverable:** API-first (`/api/v1`, authed, Swagger). React dashboard kept as a refreshed client.
- **AI/ML:** Hybrid. Stage 1 = fast multi-class TF-IDF + linear model (every request). Stage 2 = fine-tuned **DistilBERT** (Hugging Face), escalated only for uncertain cases.
- **Classes:** `benign | sql_injection | xss | path_traversal | command_injection`.
- **DB:** SQLAlchemy. SQLite (dev) / Postgres (prod via `DATABASE_URL`).
- **State:** Rate-limit + blocklist via Redis in prod; in-memory fallback for dev.

## Model answer (the question that was asked)
- Old: TF-IDF char n-grams + **LogisticRegression**, binary, SQLi-only data → real model but narrow.
- New: **Hybrid** linear screener + **DistilBERT** transformer, multi-class. Behind one interface (`app/ml/pipeline.py`) so an LLM layer can be added later without API changes.

## Honest caveats
- Dataset quality is the main driver; the old 99.5% was SQLi-only → overstated. Building a documented multi-class dataset (curated payloads + benign), not commercial threat intel.
- Regex signatures are bypassable → kept as fast precise filter; ML covers novel/obfuscated.
- "Scalable" = stateless workers + shared Redis state + Docker, not real production traffic.

## Target layout (key paths)
```
backend/app/{main,config}.py
backend/app/api/v1/{analyze,threats,config,stats,proxy,ws}.py
backend/app/core/{security,rate_limit,logging}.py   # auth, X-Forwarded-For, redis limiter
backend/app/db/{database,models,repository}.py       # SQLAlchemy
backend/app/detection/{signatures,engine}.py
backend/app/ml/{classical,transformer,pipeline,registry}.py
backend/ml_training/{data/build_dataset.py,train_classical.py,train_transformer.py,evaluate.py}
backend/tests/  Dockerfile  requirements.txt  requirements-ml.txt  .env.example
docker-compose.yml  .github/workflows/ci.yml
```

## Phase tracker
- [ ] **P0 Scaffolding** — app/ package, config.py, logging, pytest smoke. Done = `uvicorn app.main:app` /health + `pytest` green.
- [~] **P1 API + security** — backend DONE: `/api/v1/*`, API-key auth on admin, real client IP (XFF), global error handler, body-size limit, proxy timeout, repository over sqlite3. 9 pytest tests green. **Remaining:** frontend wiring (api.js + Dashboard.jsx → `/api/v1` + `X-API-Key`), README run cmd, live-server smoke check.
- [ ] **P2 Data pipeline** — `build_dataset.py` → multi-class `dataset.csv` (balanced, split, provenance).
- [ ] **P3 Stage-1 classical** — `train_classical.py` + `evaluate.py` (per-class P/R/F1). analyze returns class+confidence.
- [ ] **P4 DistilBERT + hybrid** — `train_transformer.py`, lazy transformer, escalation in `pipeline.py`, `/stats/model`.
- [ ] **P5 Scale-out** — Redis limiter+blocklist, Postgres via `DATABASE_URL`, `docker-compose.yml`.
- [ ] **P6 Tests/CI/Docker/docs** — pytest suite, Dockerfile, GitHub Actions, OpenAPI polish, README.
- [ ] **P7 Frontend refresh** — dashboard → `/api/v1` + API key, show class/confidence/model version.

## API surface (v1) — target
`GET /health` · `GET /api/v1/stats` · `GET /api/v1/stats/model` · `POST /api/v1/analyze` ·
`GET /api/v1/threats` · `POST /api/v1/threats/{id}/block|ignore` (auth) ·
`GET|POST /api/v1/config` (auth) · `GET /api/v1/export` (auth) · `POST /api/v1/demo/reset` (auth) ·
`ANY /api/v1/proxy/{path}` · `WS /api/v1/ws`

## Hybrid escalation logic (spec)
1. Signatures run first (precise, authoritative if matched).
2. Stage-1 classical predicts class + prob on every request (~1-2 ms).
3. If top prob ∈ uncertain band (~0.45–0.75) → escalate to DistilBERT (Stage 2).
4. Final verdict precedence: signature > transformer (if invoked) > classical. Reconcile confidence.

## Run commands (kept current per phase)
- Dev API: `cd backend && uvicorn app.main:app --reload` → `http://localhost:8000/docs` (today still `main:app` until P0 lands).
- Train: `pip install -r requirements-ml.txt` then `python ml_training/data/build_dataset.py && python ml_training/train_classical.py && python ml_training/train_transformer.py`.
- Frontend: `cd frontend && npm run dev` → `http://localhost:5173`.
- Stack (after P6): `docker compose up`.

## Resume here (next session) — finish P1
Backend restructure is COMPLETE and tested. To finish Phase 1, do these in order:

1. **Frontend wiring (required for dashboard to work with new backend).** All API
   calls in `frontend/src/pages/Dashboard.jsx` are hardcoded to `http://localhost:8000/<flat>`.
   - Create `frontend/src/api.js` exporting: `BASE = "http://localhost:8000/api/v1"`,
     `WS_URL = "ws://localhost:8000/api/v1/ws"`, `API_KEY = "acstd-dev-key"`, and a helper
     `apiFetch(path, opts)` that prepends BASE and sets `X-API-Key` header.
   - Update Dashboard.jsx call sites: `/health` (stays root → `http://localhost:8000/health`),
     `/threats` → `${BASE}/threats`, block/ignore → `apiFetch` (needs key), `/analyze` → `${BASE}/analyze`,
     GET+POST `/config` → `apiFetch` (now authed), `/demo/reset` → `apiFetch` (needs key),
     WS → `WS_URL`, Demo `<a>` → `${BASE}/proxy/login?demo=true`, Export `<a>` → `${BASE}/export` (open, no key).
   - Note honestly in docs: embedding API_KEY in a SPA is fine for this demo tier; real apps use user sessions.
2. **README** — change backend run cmd to `uvicorn app.main:app --reload`.
3. **Live smoke check** — start `uvicorn app.main:app`, confirm `/docs`, `/health`,
   `POST /api/v1/analyze`, and that `POST /api/v1/config` returns 401 without `X-API-Key`.
4. Tick P1 to done, then proceed to **P2 (multi-class dataset)**.

### Gotcha logged
- An orphaned process (PID 3032, the original `uvicorn main:app --reload` reloader) kept
  port 8000 in LISTEN even after kill attempts (`taskkill` said "not found" but netstat still
  showed it). Tests pass regardless (they use TestClient, no port). Tomorrow: reboot or kill
  the orphan, or just run the new server on 8000 once the stale socket clears.

## What changed in P1 (files)
- NEW: `backend/app/` package — `main.py`, `config.py`, `core/{logging,state,rate_limit,ws_manager,block_page,security,incidents}.py`,
  `db/{database,repository}.py`, `detection/{signatures,engine}.py`, `ml/{classical,pipeline}.py`, `schemas.py`,
  `api/v1/{analyze,threats,config,stats,proxy,ws,router}.py`.
- NEW: `backend/tests/` (conftest + test_health/test_analyze/test_auth) — 9 passing.
- NEW: `backend/.env.example`; updated `backend/.env` (+API_KEY, TRUSTED_PROXY_COUNT, MAX_BODY_BYTES);
  `requirements.txt` (+pydantic-settings, pytest).
- DELETED (superseded): `backend/main.py`, `detection.py`, `ml_model.py`, `database.py`.
- UPDATED callers: `simulate_traffic.py` (→ `/api/v1/analyze`), `demo_site.py` (PROXY → `/api/v1/proxy`),
  `seed.py` (import → `app.db.database`).
- NOT yet touched: `frontend/` (step 1 above).
