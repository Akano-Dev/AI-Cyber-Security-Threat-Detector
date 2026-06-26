# Installation Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- (optional) Docker + Docker Compose

## Option A — Docker (recommended for a quick stand-up)

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API + Swagger | http://localhost:8000/docs |
| Demo site (via proxy) | http://localhost:8000/api/v1/proxy/login?demo=true |

Override the admin key:

```bash
API_KEY=$(openssl rand -hex 16) docker compose up --build
```

Stop with `docker compose down`. The SQLite DB is in-container and ephemeral;
add a volume to `backend` if you want persistence.

## Option B — Manual (development)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:  .\.venv\Scripts\Activate.ps1
# macOS/Linux:         source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # then set a real API_KEY
python train.py               # builds model.pkl + metrics.json (optional but recommended)
uvicorn app.main:app --reload # http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

### 3. (optional) Demo target + traffic

```bash
cd backend
python demo_site.py                       # fake intranet on :8090
python simulate_traffic.py                # mixed synthetic traffic
python simulate_traffic.py --scenario port_scan --ports 12
```

## Option C — Hugging Face Spaces (backend API)

See [`deploy/huggingface/README.md`](../deploy/huggingface/README.md). In short:
create a **Docker** Space, place `backend/` at its root with the provided front
matter, and set `API_KEY` / `CORS_ORIGINS` as Space secrets.

## Configuration (env / `.env`)

| Var | Default | Purpose |
|---|---|---|
| `API_KEY` | `acstd-dev-key` | Admin key for mutating endpoints — **change it** |
| `TARGET_URL` | `http://localhost:8090` | Proxy forward target (empty disables) |
| `RATE_LIMIT` / `RATE_WINDOW` | `20` / `60` | Auto-block threshold |
| `TRUSTED_PROXY_COUNT` | `0` | Trusted reverse proxies for real client IP |
| `MAX_BODY_BYTES` | `1000000` | Reject larger request bodies |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed dashboard origins |
| `DB_PATH` / `MODEL_PATH` / `METRICS_PATH` | under `backend/` | Artifact paths |

## Verify

```bash
curl http://localhost:8000/health          # {"status":"ok"}
curl http://localhost:8000/api/v1/version
cd backend && python -m pytest -q           # 9 passed
```
