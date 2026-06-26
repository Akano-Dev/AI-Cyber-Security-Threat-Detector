// Central backend config + fetch helper for the ACSTD API (v1).
//
// Note: shipping the admin API key inside a SPA is acceptable for this demo
// tier — anyone with the dashboard can already act on it. A real deployment
// would use per-user sessions, not one shared key baked into the browser bundle.

const HOST = "http://localhost:8000";

export const BASE = `${HOST}/api/v1`;
export const WS_URL = `${HOST.replace(/^http/, "ws")}/api/v1/ws`;
export const HEALTH_URL = `${HOST}/health`; // health check lives at the root, not under /api/v1
export const API_KEY = "acstd-dev-key";

// fetch wrapper for endpoints under /api/v1: prepends BASE and attaches the
// admin API key. Use this for the authed routes (block / ignore / config /
// demo reset); plain `${BASE}/...` fetches are fine for the open ones.
export function apiFetch(path, opts = {}) {
  return fetch(`${BASE}${path}`, {
    ...opts,
    headers: { ...(opts.headers || {}), "X-API-Key": API_KEY },
  });
}
