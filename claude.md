# Project: AI Cyber Security Threat Detector

## What this is
A defensive web app that detects web-based cyber threats in real time and lets a
user block or ignore them. It is a security monitoring dashboard, built as an
internship demo project.

## Stack
- Backend: Python + FastAPI, SQLite database
- Frontend: React + Vite
- Real-time: WebSockets (via FastAPI)
- AI/ML: scikit-learn (added in a later phase)

## How it works (architecture)
- The backend exposes an /analyze endpoint that inspects incoming request data
  and classifies it as THREAT or SAFE using (1) signature rules and later (2) an
  ML model.
- Detected threats are saved in SQLite and pushed live to the dashboard over a
  WebSocket.
- The React dashboard shows a live feed of threats, summary stats, and
  Block / Ignore buttons.
- A traffic simulator generates a mix of normal and malicious traffic so the
  dashboard has data during the demo.

## Threat types to handle
SQL injection, XSS, path traversal, command injection, suspicious user-agents,
brute-force / rate abuse.

## Rules for you (Claude)
- Keep code simple and readable — this is a student project.
- Keep your replies SHORT. Do not explain unless I ask.
- Only create or modify the files needed for the current task.
- After each task, tell me the exact commands to run and what I should see.