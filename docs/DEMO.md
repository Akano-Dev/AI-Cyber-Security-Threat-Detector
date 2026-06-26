# Demo Guide (5 minutes)

A concise script for presenting ACSTD. For the long-form walkthrough see
[`HOW_TO_RUN_AND_DEMO.txt`](../HOW_TO_RUN_AND_DEMO.txt).

## Setup

Have these running (Docker: `docker compose up --build` covers backend + demo +
frontend in one go):

1. Backend — `uvicorn app.main:app --reload` (`:8000`)
2. Frontend — `npm run dev` (`:5173`)
3. Demo site — `python demo_site.py` (`:8090`)

Optionally pre-seed history: `python seed.py`.

## Script

1. **The dashboard.** Open http://localhost:5173. Point out the live feed, stat
   cards, threats-by-type chart, and the **Live** WebSocket indicator.

2. **A protected site.** Open
   http://localhost:8000/api/v1/proxy/login?demo=true — a fake "IntraPortal"
   intranet behind ACSTD's inspecting proxy. Note the demo banner + the
   floating **Attack Simulator** panel.

3. **Catch an attack live.** Click the red **SQL Injection** button — it
   auto-fills `' OR '1'='1` and submits. Switch to the dashboard: a new
   **HIGH** SQL Injection row appears instantly with payload + confidence.
   Repeat with **XSS** and **Path Traversal** on the other pages.

4. **Analyst responds.** Click **Block** on a row, then re-run the same attack —
   it now returns **blocked** before detection even runs. Click **Ignore** on
   another row to show triage.

5. **It's a real API.** Open http://localhost:8000/docs and "Try it out" on
   `POST /api/v1/analyze`. Show `GET /api/v1/stats/model` (model + metrics) and
   `GET /api/v1/metrics` (live request counters).

6. **Scale + variety.** In a terminal:
   ```bash
   python simulate_traffic.py                       # mixed stream
   python simulate_traffic.py --scenario rate_abuse --burst 30   # triggers auto-block
   python simulate_traffic.py --scenario port_scan --ports 12    # scanner UAs
   ```
   Watch the feed light up.

7. **Reports.** `GET /api/v1/export` downloads a CSV incident report.

## Reset between runs

Click **Reset Demo** in the dashboard, or:

```bash
curl -X POST http://localhost:8000/api/v1/demo/reset -H "X-API-Key: acstd-dev-key"
```

## Talking points (be honest)

- Detection is **hybrid**: precise regex signatures + an ML model for novel
  payloads.
- The bundled model is SQLi-trained, so it's strongest on SQLi; other classes
  lean on signatures. A multi-class model exists but isn't wired in yet.
- "Port scan" surfaces as **Suspicious User-Agent** because this backend
  inspects HTTP payloads/UAs, not packets.
