---
title: ACSTD API
emoji: 🛡️
colorFrom: indigo
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# ACSTD — Deploying the API to Hugging Face Spaces (Docker SDK)

This deploys the **backend API + Swagger UI** as a Docker Space. The React
dashboard is a separate static deploy (Vercel/Netlify/Pages) or runs locally.

> Hugging Face reads the YAML front matter **above** from the Space's root
> `README.md`. `app_port: 7860` matches the port the container listens on.

## Steps

1. Create a new Space → **Docker** → blank template.
2. Put the **backend** at the Space root so its `Dockerfile` is found:
   - Copy the contents of this repo's `backend/` to the Space root, **and**
   - Copy the front matter above into the Space's root `README.md`.
   (Alternatively, keep the repo as-is and set the Space's Dockerfile path to
   `backend/Dockerfile` via a root Dockerfile that `FROM`s it.)
3. Set **Space secrets / variables** (Settings → Variables and secrets):
   - `API_KEY` — a strong random value (do **not** ship `acstd-dev-key`).
   - `CORS_ORIGINS` — JSON list incl. your dashboard origin, e.g.
     `["https://your-dashboard.vercel.app"]`.
   - `TARGET_URL` — optional proxy target (leave empty to disable the proxy).
4. Push. The Space builds the image, bakes the model (`train.py`), and serves:
   - `https://<user>-<space>.hf.space/docs` — Swagger UI
   - `https://<user>-<space>.hf.space/health` — liveness
   - `https://<user>-<space>.hf.space/api/v1/version` — version

## Notes

- The Space filesystem is **ephemeral** — `threats.db` resets on rebuild/restart.
  Fine for a demo; use a managed Postgres for persistence (see checklist).
- The dashboard must point at the Space URL. Today that host is hard-coded in
  `frontend/src/api.js`; make it an env var before deploying the frontend
  remotely (tracked in `PRODUCTION_CHECKLIST.md`).
