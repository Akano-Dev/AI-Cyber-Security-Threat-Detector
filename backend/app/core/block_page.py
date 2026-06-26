"""Branded HTML block page returned by the proxy when a request is denied."""
from fastapi.responses import Response


def block_page(status: int, title: str, detail: str) -> Response:
    color = "#ef4444" if status == 403 else "#f59e0b"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{status} — Blocked</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
      background: #050c18;
      background-image:
        linear-gradient(rgba(6,182,212,.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(6,182,212,.04) 1px, transparent 1px);
      background-size: 40px 40px;
      font-family: system-ui, sans-serif; color: #f1f5f9;
    }}
    .card {{
      background: #0c1520; border: 1px solid #1a2d45; border-radius: 20px;
      padding: 48px 56px; max-width: 480px; width: 90%; text-align: center;
      box-shadow: 0 0 60px rgba(6,182,212,.05);
    }}
    .badge {{
      display: inline-flex; align-items: center; gap: 8px;
      background: {color}18; color: {color}; border: 1px solid {color}30;
      border-radius: 999px; padding: 6px 16px; font-size: 12px; font-weight: 700;
      letter-spacing: .08em; text-transform: uppercase; margin-bottom: 24px;
    }}
    .dot {{ width: 7px; height: 7px; background: {color}; border-radius: 50%;
      animation: pulse 1.8s ease-in-out infinite; }}
    @keyframes pulse {{ 0%,100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: .4; transform: scale(1.5); }} }}
    h1 {{ font-size: 56px; font-weight: 800; color: {color}; letter-spacing: -.02em; line-height: 1; margin-bottom: 12px; }}
    h2 {{ font-size: 18px; font-weight: 600; color: #e2e8f0; margin-bottom: 12px; }}
    p {{ font-size: 14px; color: #64748b; line-height: 1.6; }}
    .divider {{ border: none; border-top: 1px solid #1a2d45; margin: 28px 0; }}
    .brand {{ font-size: 12px; color: #334155; letter-spacing: .06em; }}
    .brand span {{ color: #06b6d4; font-weight: 700; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge"><span class="dot"></span>Access Denied</div>
    <h1>{status}</h1>
    <h2>{title}</h2>
    <p>{detail}</p>
    <hr class="divider" />
    <p class="brand">Protected by <span>ACSTD</span> · AI Cyber Security Threat Detector</p>
  </div>
</body>
</html>"""
    return Response(content=html, status_code=status, media_type="text/html")
