# Production-Readiness Checklist

Final review of ACSTD for deployment. Legend: ✅ done · ⚠️ partial · ❌ open ·
**[code]** = needs an application change (intentionally deferred — deployment
prep does not modify functionality).

This is a **demo/student project**. The checklist is honest about what is and
isn't ready, so reviewers can judge it fairly.

## Security

| Status | Item | Notes |
|---|---|---|
| ✅ | API-key auth on mutating endpoints | `X-API-Key` on block/ignore/config/reset |
| ✅ | `.gitignore` + secrets/artifacts untracked | added this engagement |
| ✅ | Input validation + body-size limit | bounded fields, `MAX_BODY_BYTES` |
| ✅ | Restricted CORS, parameterized SQL, escaped demo output | — |
| ⚠️ | Rotate the API key | default `acstd-dev-key` is in **git history** + the SPA bundle; rotate before any real deploy |
| ❌ | Purge secret from git history | `git filter-repo`/BFG + key rotation |
| ❌ | Authn on read endpoints (`/threats`, `/export`) **[code]** | `/export` leaks all stored data unauthenticated |
| ❌ | `/analyze` trusts client `source_ip` **[code]** | spoofable; enables blocklist poisoning |
| ❌ | TLS + security headers (CSP/HSTS) | terminate TLS at a proxy; add headers |
| ❌ | Constant-time key compare **[code]** | minor timing side-channel |

## Reliability & correctness

| Status | Item | Notes |
|---|---|---|
| ✅ | Global error handler + request IDs | `X-Request-ID`, 500 carries `request_id` |
| ❌ | SQLite connection leak **[code]** | `with get_conn()` never closes — top reliability fix |
| ❌ | WebSocket auto-reconnect **[code]** | dashboard freezes silently after a drop |
| ❌ | Rate-limiter unbounded memory **[code]** | per-IP deques never evicted |
| ❌ | Proxy passes upstream encoding headers **[code]** | can corrupt gzipped responses |

## Deployment

| Status | Item | Notes |
|---|---|---|
| ✅ | Backend Dockerfile (non-root, bakes model, `$PORT`) | `backend/Dockerfile` |
| ✅ | Frontend Dockerfile + nginx SPA serve | `frontend/Dockerfile`, `nginx.conf` |
| ✅ | `docker-compose.yml` (backend + demo + frontend) | local prod-like stack |
| ✅ | Hugging Face Spaces config | `deploy/huggingface/README.md` (Docker SDK, `app_port 7860`) |
| ❌ | Configurable frontend API host **[code]** | `api.js` hard-codes `localhost:8000` — blocks remote SPA deploy |
| ❌ | Persistent datastore | container SQLite is ephemeral; use Postgres for real use |
| ❌ | CI pipeline | run pytest + build images on push |

## Observability

| Status | Item | Notes |
|---|---|---|
| ✅ | `/health` + `/health/ready` diagnostics | liveness + DB/model readiness (503 if DB down) |
| ✅ | `/version` + `/metrics` | uptime, request counts, latency, totals |
| ✅ | Structured logging + slow-request logging | `core/logging.py`, observe middleware |
| ❌ | External metrics/log aggregation | Prometheus/OTel exporter for multi-worker |

## Performance & scale

| Status | Item | Notes |
|---|---|---|
| ❌ | DB indexes on `status`/`source_ip`/`timestamp` **[code]** | see PERFORMANCE.md |
| ❌ | Pagination on `/threats` + `/export` **[code]** | unbounded reads |
| ❌ | Shared state via Redis (blocklist/rate-limit/WS) **[code]** | required before multi-worker |
| ❌ | Frontend table virtualization **[code]** | grows unbounded |

## ML

| Status | Item | Notes |
|---|---|---|
| ✅ | Stage-1 model trains + loads; `/stats/model` exposes metrics | SQLi-trained binary |
| ✅ | Multi-class model built + verified (RF, 5 classes) | `train_multiclass.py`; **not wired in** |
| ⚠️ | Honest metrics | SQLi-only accuracy is not general performance |
| ❌ | Wire multi-class model behind `pipeline.predict()` **[code]** | integration step |
| ❌ | Train on real, diverse payload corpora | synthetic data inflates scores |

## Documentation

| Status | Item | Notes |
|---|---|---|
| ✅ | README, INSTALL, DEMO, ARCHITECTURE, API, PERFORMANCE | this engagement |
| ✅ | Swagger/OpenAPI complete (14 paths, tags, examples) | `/docs` |
| ⚠️ | Screenshots | folder + capture guide added; PNGs to be captured |
| ⚠️ | Stale `TECH_USED.txt` references removed | still references deleted files |

## Go / No-go summary

**Demo deploy (single worker, HF Space / compose):** ✅ ready — set a strong
`API_KEY` + correct `CORS_ORIGINS`, accept ephemeral data.

**Public/multi-user deploy:** ❌ not yet — close the **[code]** security items
(unauth `/export`, `source_ip` trust, connection leak), make the frontend host
configurable, rotate the leaked key, and move shared state to Redis + Postgres.

### Recommended next order

1. SQLite connection leak (reliability).
2. Rotate `API_KEY` + make frontend host configurable (deploy blockers).
3. Auth/scope `/export` + `/analyze` hardening (security).
4. DB indexes + pagination (performance).
5. Wire in the multi-class model (ML).
