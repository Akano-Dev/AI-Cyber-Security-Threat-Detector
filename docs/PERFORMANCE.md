# Performance & Scaling Notes

Honest guidance for taking ACSTD beyond a single-machine demo. Items marked
**[code]** require application changes (deferred during deployment prep).

## Current characteristics

- Detection is cheap: regex + a TF-IDF/logreg `predict` (~1–2 ms/payload).
- The bottlenecks are I/O and unbounded growth, not the model.

## Database

- **Add indexes** on `threats(status)`, `threats(source_ip)`,
  `threats(timestamp)` — `/stats` and filtered reads currently full-scan. **[code]**
- **Paginate `/threats` and `/export`** — both return *all* rows today; this
  grows unbounded with the simulator running. **[code]**
- **Fix the connection leak** — `with get_conn()` commits but never closes;
  connections accumulate. Use a context manager that closes, or a pool. **[code]**
- For real load, move SQLite → **Postgres** via `DATABASE_URL` (planned P5).

## Application server

- Run under multiple workers: `uvicorn app.main:app --workers 4` or
  `gunicorn -k uvicorn.workers.UvicornWorker`.
- ⚠️ **State is per-worker**: the blocklist, rate-limiter, WebSocket clients,
  and `/metrics` counters are in-memory. With >1 worker they diverge. Move
  blocklist + rate-limit to **Redis** before scaling out. **[code]**

## Real-time

- WebSocket broadcast is O(clients) per event — fine for a dashboard, not for
  thousands of subscribers. A pub/sub (Redis) backplane fixes multi-worker fan-out.
- The dashboard **does not auto-reconnect** after a drop — add backoff reconnect. **[code]**

## Frontend

- Serve the built SPA from a CDN/static host (the provided nginx image is a
  start); enable gzip/brotli.
- **Virtualize / paginate the threat table** — it re-renders an ever-growing
  list. **[code]**
- The API host is hard-coded (`api.js`); make it an env var so the bundle isn't
  rebuilt per environment. **[code]**

## Caching & limits

- `/stats` recomputes counters in Python each call — cache for a few seconds or
  compute via SQL aggregates. **[code]**
- Body-size limit only checks `Content-Length`; chunked uploads bypass it. **[code]**

## Quick wins for a demo deploy

1. `--workers 1` (keeps in-memory state coherent) behind a reverse proxy.
2. Add DB indexes (one migration).
3. Put nginx/CDN in front of the SPA with gzip.
4. Set a strong `API_KEY` and correct `CORS_ORIGINS`.
