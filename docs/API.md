# API Reference

Base URL (local): `http://localhost:8000`  ·  Interactive docs:
`http://localhost:8000/docs` (Swagger) and `/redoc`.

All versioned routes live under `/api/v1`. `/health*` lives at the root.

## Authentication

Admin/mutating endpoints require a header:

```
X-API-Key: <API_KEY>     # default "acstd-dev-key" — override via env in any real deploy
```

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Liveness probe → `{"status":"ok"}` |
| GET | `/health/ready` | — | Readiness diagnostics (DB, model); 503 if DB down |
| GET | `/api/v1/version` | — | Service name, version, uptime |
| GET | `/api/v1/metrics` | — | Runtime metrics (requests, latency, totals) |
| POST | `/api/v1/analyze` | — | Classify one payload |
| GET | `/api/v1/threats` | — | List logged threats |
| POST | `/api/v1/threats/{id}/block` | ✅ | Block the threat's source IP |
| POST | `/api/v1/threats/{id}/ignore` | ✅ | Mark a threat ignored |
| GET | `/api/v1/stats` | — | Counts by type / severity / status |
| GET | `/api/v1/stats/model` | — | ML model metadata + metrics |
| GET | `/api/v1/config` | ✅ | Read proxy + rate-limit config |
| POST | `/api/v1/config` | ✅ | Update proxy + rate-limit config |
| GET | `/api/v1/export` | — | Download CSV incident report |
| POST | `/api/v1/demo/reset` | ✅ | Clear threats + unblock all IPs |
| ANY | `/api/v1/proxy/{path}` | — | Inspecting reverse proxy |
| WS | `/api/v1/ws` | — | Live threat event stream |

Every response carries an `X-Request-ID` header for correlation.

## `threat_type` values

`SQL Injection` · `XSS` · `Path Traversal` · `Command Injection` ·
`Suspicious User-Agent` · `Brute Force / Rate Abuse` · `Anomalous Payload`
(ML-only). The dashboard colour-maps each of these.

## Examples

Classify a payload:

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"source_ip":"203.0.113.5","payload":"'"'"' OR 1=1 --","user_agent":"sqlmap/1.7"}'
# -> {"verdict":"threat","threat_type":"SQL Injection","severity":"high","confidence":...}
```

Block an IP (admin):

```bash
curl -X POST http://localhost:8000/api/v1/threats/1/block -H "X-API-Key: acstd-dev-key"
```

Runtime metrics:

```bash
curl http://localhost:8000/api/v1/metrics
# -> {"uptime_seconds":..,"requests_total":..,"avg_response_ms":..,"threats_total":..,
#     "blocked_ips":..,"ws_clients":..,"model_loaded":true}
```

WebSocket events (shapes):

```jsonc
{"event":"new_threat","id":12,"timestamp":"...","source_ip":"...","threat_type":"XSS",
 "payload":"...","severity":"medium","status":"new","confidence":76}
{"event":"status_update","id":12,"status":"blocked"}
{"event":"demo_reset"}
```

## Errors

- `401` — missing/invalid `X-API-Key` on admin routes.
- `404` — unknown threat id.
- `413` — request body exceeds `MAX_BODY_BYTES`.
- `422` — validation error (e.g. empty `payload`, `rate_limit < 1`).
- `500` — `{"detail":"Internal server error","request_id":"..."}`.
