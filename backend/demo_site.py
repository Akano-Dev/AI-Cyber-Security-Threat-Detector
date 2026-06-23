"""
ACSTD Demo Site — a fictional corporate intranet with intentionally vulnerable pages.
Runs on port 8080. All form submissions route through ACSTD proxy on port 8000.
Start with: python demo_site.py
"""

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import html as h

app = FastAPI(docs_url=None, redoc_url=None)

PROXY = "http://localhost:8000/proxy"

# ── In-memory data ───────────────────────────────────────────────────────────

_comments = [
    {"author": "Alice Johnson",  "text": "Welcome to IntraPortal! Please read the updated security policy.", "time": "09:15"},
    {"author": "Bob Smith",      "text": "Reminder: all-hands meeting at 3 PM in Conference Room B.",        "time": "10:30"},
    {"author": "Carol Davis",    "text": "Q4 expense reports due Friday — use the new self-service portal.",  "time": "11:45"},
]

_employees = [
    {"name": "Alice Johnson", "dept": "Engineering", "email": "alice@intra.corp", "ext": "x4521"},
    {"name": "Bob Smith",     "dept": "Marketing",   "email": "bob@intra.corp",   "ext": "x3812"},
    {"name": "Carol Davis",   "dept": "Finance",     "email": "carol@intra.corp", "ext": "x5203"},
    {"name": "David Chen",    "dept": "Engineering", "email": "david@intra.corp", "ext": "x4890"},
    {"name": "Eva Martinez",  "dept": "HR",          "email": "eva@intra.corp",   "ext": "x2341"},
    {"name": "Frank Wilson",  "dept": "Security",    "email": "frank@intra.corp", "ext": "x6120"},
]

# ── Shared CSS ───────────────────────────────────────────────────────────────

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#f1f5f9;color:#0f172a;min-height:100vh}
.header{background:linear-gradient(135deg,#1e3a5f,#1e40af);color:#fff;padding:0 32px;height:60px;
  display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 12px rgba(0,0,0,.25)}
.brand{font-size:19px;font-weight:800;letter-spacing:-.02em;display:flex;align-items:center;gap:9px}
.brand-dot{width:8px;height:8px;background:#38bdf8;border-radius:50%}
nav{display:flex;gap:4px}
nav a{color:rgba(255,255,255,.7);text-decoration:none;padding:7px 13px;border-radius:8px;
  font-size:13px;font-weight:500;transition:.15s}
nav a:hover,nav a.active{color:#fff;background:rgba(255,255,255,.14)}
.main{max-width:800px;margin:44px auto;padding:0 24px}
.card{background:#fff;border-radius:16px;box-shadow:0 1px 3px rgba(0,0,0,.07),0 4px 16px rgba(0,0,0,.05);padding:40px}
.card h2{font-size:22px;font-weight:700;margin-bottom:6px}
.sub{color:#64748b;font-size:14px;margin-bottom:28px}
label{display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:5px}
input[type=text],input[type=password],input[type=search],textarea{
  width:100%;padding:10px 13px;border:1.5px solid #e2e8f0;border-radius:10px;
  font-size:14px;outline:none;transition:.15s;background:#f8fafc;color:#0f172a;font-family:inherit}
input:focus,textarea:focus{border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.1);background:#fff}
textarea{resize:vertical;min-height:88px}
.fg{margin-bottom:18px}
.btn{display:inline-flex;align-items:center;gap:7px;padding:10px 22px;border:none;
  border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;transition:.15s}
.btn-p{background:#2563eb;color:#fff}.btn-p:hover{background:#1d4ed8}
.alert{padding:13px 16px;border-radius:10px;font-size:14px;margin-bottom:20px;line-height:1.55}
.ok{background:#f0fdf4;border-left:3px solid #16a34a;color:#15803d}
.err{background:#fef2f2;border-left:3px solid #dc2626;color:#b91c1c}
.inf{background:#eff6ff;border-left:3px solid #3b82f6;color:#1e40af}
table{width:100%;border-collapse:collapse;margin-top:20px;font-size:13.5px}
th{text-align:left;padding:9px 13px;background:#f8fafc;border-bottom:2px solid #e2e8f0;
  font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#64748b}
td{padding:11px 13px;border-bottom:1px solid #f1f5f9;color:#334155}
tr:hover td{background:#fafbff}
.comment{padding:14px 0;border-bottom:1px solid #f1f5f9}
.comment:last-child{border-bottom:none}
.cmeta{font-size:12px;color:#94a3b8;margin-bottom:3px}
.cmeta strong{color:#334155;font-weight:600}
.cbody{font-size:14px;color:#334155;line-height:1.6}
code{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-family:monospace;font-size:12px;color:#0369a1}
.hint{font-size:12px;color:#94a3b8;margin-top:5px}

/* ── Demo banner ── */
.demo-banner{background:linear-gradient(90deg,#7c3aed,#4f46e5);color:#fff;
  text-align:center;padding:8px;font-size:13px;font-weight:700;letter-spacing:.04em}
.demo-banner em{font-style:normal;opacity:.65;margin:0 10px}

/* ── Demo attack panel ── */
.dp{position:fixed;bottom:20px;right:20px;width:296px;background:#0f172a;
  border:1px solid #1e293b;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.5);z-index:999;overflow:hidden}
.dp-head{background:#1e293b;padding:13px 16px;display:flex;align-items:center;gap:9px}
.dp-head span{color:#f1f5f9;font-size:13.5px;font-weight:700;flex:1}
.dp-head .live{width:7px;height:7px;border-radius:50%;background:#ef4444;
  animation:blink 1.4s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.dp-body{padding:12px;display:flex;flex-direction:column;gap:7px}
.ab{width:100%;padding:9px 13px;border:none;border-radius:8px;cursor:pointer;
  font-size:12.5px;font-weight:600;text-align:left;display:flex;align-items:center;gap:9px;transition:.12s}
.ab .sev{font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;margin-left:auto;flex-shrink:0}
.ab.sqli{background:#450a0a;color:#fca5a5}.ab.sqli:hover{background:#7f1d1d}
.ab.sqli .sev{background:#dc2626;color:#fff}
.ab.xss{background:#431407;color:#fed7aa}.ab.xss:hover{background:#7c2d12}
.ab.xss .sev{background:#ea580c;color:#fff}
.ab.cmd{background:#2d1b00;color:#fde68a}.ab.cmd:hover{background:#78350f}
.ab.cmd .sev{background:#d97706;color:#fff}
.ab.pt{background:#1a1a2e;color:#c4b5fd}.ab.pt:hover{background:#2d1b69}
.ab.pt .sev{background:#7c3aed;color:#fff}
.ab.safe{background:#052e16;color:#86efac}.ab.safe:hover{background:#14532d}
.ab.safe .sev{background:#16a34a;color:#fff}
.dp-tip{font-size:11px;color:#475569;padding:0 12px 12px;line-height:1.5}
"""

# ── HTML helpers ─────────────────────────────────────────────────────────────

def _nav(active="", demo=False):
    dm = "?demo=true" if demo else ""
    def lnk(href, label, key):
        cls = "active" if active == key else ""
        return f'<a href="{PROXY}/{href}{dm}" class="{cls}">{label}</a>'
    return f"""
    <div class="header">
      <div class="brand"><div class="brand-dot"></div>IntraPortal</div>
      <nav>
        {lnk("login","🔐 Login","login")}
        {lnk("search","🔍 Employee Search","search")}
        {lnk("comments","💬 Bulletin Board","comments")}
      </nav>
    </div>"""

def _demo_panel(page="login"):
    # (css_class, label, severity_badge, payload, field_id, extra_field, extra_val)
    attacks = {
        "login": [
            ("sqli", "SQL Injection",  "HIGH", "' OR '1'='1",               "username_field", "",         ""),
            ("sqli", "SQLi (DROP)",    "HIGH", "admin'; DROP TABLE users--", "username_field", "",         ""),
            ("safe", "Normal Login",   "SAFE", "admin",                      "username_field", "pwd_field", "password123"),
        ],
        "search": [
            ("xss",  "XSS Script Tag", "HIGH", "<script>alert('XSS')</script>", "search_field", "", ""),
            ("xss",  "XSS Event",      "HIGH", '"><img src=x onerror=alert(1)>', "search_field", "", ""),
            ("pt",   "Path Traversal", "MED",  "../../etc/passwd",               "search_field", "", ""),
            ("safe", "Normal Search",  "SAFE", "engineering",                    "search_field", "", ""),
        ],
        "comments": [
            ("xss",  "Stored XSS",    "HIGH", "<script>document.cookie</script>",  "comment_field", "", ""),
            ("cmd",  "Cmd Injection",  "HIGH", "Great post; cat /etc/passwd",        "comment_field", "", ""),
            ("xss",  "XSS Image",      "HIGH", '<img src=x onerror=alert("hacked")>', "comment_field", "", ""),
            ("safe", "Normal Comment", "SAFE", "Great update, thanks team!",          "comment_field", "", ""),
        ],
    }
    btns = ""
    for cls, label, sev, payload, field_id, extra_field, extra_val in attacks.get(page, []):
        btns += f"""
        <button class="ab {cls}" onclick="fillAndSubmit('{field_id}',`{payload}`,'{extra_field}','{extra_val}')">
          {label}<span class="sev">{sev}</span>
        </button>"""

    return f"""
    <div class="dp">
      <div class="dp-head"><div class="live"></div><span>⚡ Attack Simulator</span></div>
      <div class="dp-body">{btns}</div>
      <div class="dp-tip">Click an attack to auto-fill and submit. Watch the ACSTD dashboard for live detection.</div>
    </div>
    <script>
    function fillAndSubmit(id, val, id2, val2) {{
      var el = document.getElementById(id);
      if (el) el.value = val;
      if (id2) {{ var el2 = document.getElementById(id2); if (el2) el2.value = val2; }}
      if (el) el.closest('form').submit();
    }}
    </script>"""

def _page(title, body, demo=False, active="", page="login"):
    banner = '<div class="demo-banner">⚡ DEMO MODE <em>|</em> ACSTD Threat Detector Active <em>|</em> Open dashboard at localhost:5173</div>' if demo else ""
    panel  = _demo_panel(page) if demo else ""
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — IntraPortal</title><style>{_CSS}</style></head>
<body>{banner}{_nav(active, demo)}
<div class="main">{body}</div>
{panel}</body></html>"""

def _dm(demo):
    return "true" if demo else "false"

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(demo: bool = False):
    return RedirectResponse(url=f"{PROXY}/login{'?demo=true' if demo else ''}")

# ── Login ────────────────────────────────────────────────────────────────────

def _login_form(demo=False, msg=""):
    return f"""
    <div class="card">
      <h2>🔐 Employee Login</h2>
      <p class="sub">Sign in with your corporate credentials to access IntraPortal.</p>
      {msg}
      <form method="POST" action="{PROXY}/login">
        <input type="hidden" name="demo" value="{_dm(demo)}">
        <div class="fg"><label>Username</label>
          <input type="text" name="username" id="username_field" placeholder="e.g. admin" autocomplete="off">
          <p class="hint">Try: <code>admin</code></p></div>
        <div class="fg"><label>Password</label>
          <input type="password" name="password" id="pwd_field" placeholder="••••••••">
          <p class="hint">Try: <code>password123</code></p></div>
        <button type="submit" class="btn btn-p">Sign In →</button>
      </form>
    </div>"""

@app.get("/login", response_class=HTMLResponse)
async def login_get(demo: bool = False):
    return HTMLResponse(_page("Login", _login_form(demo), demo=demo, active="login", page="login"))

@app.post("/login", response_class=HTMLResponse)
async def login_post(demo: str = Form("false"), username: str = Form(""), password: str = Form("")):
    is_demo = demo == "true"
    safe_user = h.escape(username)
    if username == "admin" and password == "password123":
        msg = f'<div class="alert ok">✅ Welcome back, <strong>{safe_user}</strong>! You are logged in as Administrator.</div>'
    else:
        msg = f'<div class="alert err">❌ Invalid credentials for <strong>{safe_user}</strong>. Hint: <code>admin / password123</code></div>'
    return HTMLResponse(_page("Login", _login_form(is_demo, msg), demo=is_demo, active="login", page="login"))

# ── Search ───────────────────────────────────────────────────────────────────

def _search_form(demo=False, msg="", results=None):
    rows = ""
    if results is not None:
        for e in results:
            rows += f"<tr><td>{h.escape(e['name'])}</td><td>{e['dept']}</td><td>{e['email']}</td><td>{e['ext']}</td></tr>"
        table = f"""<table><thead><tr><th>Name</th><th>Department</th><th>Email</th><th>Ext.</th></tr></thead>
        <tbody>{rows if rows else '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:24px">No employees found.</td></tr>'}</tbody></table>"""
    else:
        table = ""
    return f"""
    <div class="card">
      <h2>🔍 Employee Directory</h2>
      <p class="sub">Search for employees by name or department.</p>
      {msg}
      <form method="POST" action="{PROXY}/search">
        <input type="hidden" name="demo" value="{_dm(demo)}">
        <div class="fg" style="display:flex;gap:10px;align-items:flex-end">
          <div style="flex:1">
            <label>Search</label>
            <input type="search" name="q" id="search_field" placeholder="Name or department…" autocomplete="off">
          </div>
          <button type="submit" class="btn btn-p" style="white-space:nowrap">Search →</button>
        </div>
      </form>
      {table}
    </div>"""

@app.get("/search", response_class=HTMLResponse)
async def search_get(demo: bool = False):
    return HTMLResponse(_page("Employee Search", _search_form(demo), demo=demo, active="search", page="search"))

@app.post("/search", response_class=HTMLResponse)
async def search_post(demo: str = Form("false"), q: str = Form("")):
    is_demo = demo == "true"
    sq = q.lower().strip()
    results = [e for e in _employees if sq in e["name"].lower() or sq in e["dept"].lower()] if sq else _employees
    msg = f'<div class="alert inf">🔍 Showing results for: <strong>{h.escape(q)}</strong> — {len(results)} found</div>' if q else ""
    return HTMLResponse(_page("Employee Search", _search_form(is_demo, msg, results), demo=is_demo, active="search", page="search"))

# ── Comments ─────────────────────────────────────────────────────────────────

def _comments_form(demo=False, msg=""):
    items = "".join(f"""
    <div class="comment">
      <div class="cmeta"><strong>{h.escape(c['author'])}</strong> · {c['time']}</div>
      <div class="cbody">{h.escape(c['text'])}</div>
    </div>""" for c in reversed(_comments))

    return f"""
    <div class="card">
      <h2>💬 Bulletin Board</h2>
      <p class="sub">Post announcements and updates for the whole team.</p>
      {msg}
      <form method="POST" action="{PROXY}/comments" style="margin-bottom:32px">
        <input type="hidden" name="demo" value="{_dm(demo)}">
        <div class="fg"><label>Your Name</label>
          <input type="text" name="author" placeholder="e.g. John Doe" autocomplete="off"></div>
        <div class="fg"><label>Message</label>
          <textarea name="comment" id="comment_field"
            placeholder="Write something for the team…"></textarea></div>
        <button type="submit" class="btn btn-p">Post →</button>
      </form>
      <div>{items}</div>
    </div>"""

@app.get("/comments", response_class=HTMLResponse)
async def comments_get(demo: bool = False):
    return HTMLResponse(_page("Bulletin Board", _comments_form(demo), demo=demo, active="comments", page="comments"))

@app.post("/comments", response_class=HTMLResponse)
async def comments_post(demo: str = Form("false"), author: str = Form("Anonymous"), comment: str = Form("")):
    is_demo = demo == "true"
    if comment.strip():
        from datetime import datetime
        _comments.append({"author": author or "Anonymous", "text": comment, "time": datetime.now().strftime("%H:%M")})
        msg = '<div class="alert ok">✅ Comment posted successfully.</div>'
    else:
        msg = '<div class="alert err">❌ Comment cannot be empty.</div>'
    return HTMLResponse(_page("Bulletin Board", _comments_form(is_demo, msg), demo=is_demo, active="comments", page="comments"))


if __name__ == "__main__":
    print("🌐  IntraPortal demo site  →  http://localhost:8090")
    print("🛡   Access through ACSTD  →  http://localhost:8000/proxy/login")
    print("⚡   Demo mode             →  http://localhost:8000/proxy/login?demo=true")
    uvicorn.run("demo_site:app", host="0.0.0.0", port=8090, reload=True)
