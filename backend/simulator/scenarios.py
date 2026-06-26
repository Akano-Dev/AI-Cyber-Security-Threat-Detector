"""Reusable simulation scenarios.

Each scenario is a generator function yielding `Event`s. A single-shot attack
yields one event; burst scenarios (rate abuse, port scan) yield several. The
runner sends each event and honours its intra-burst `gap`.
"""
import random
from dataclasses import dataclass

from . import generators as g


@dataclass
class Event:
    category: str       # display label, e.g. "SQL Injection"
    payload: str
    user_agent: str
    source_ip: str
    gap: float = 0.0    # seconds to wait after sending (intra-burst pacing)


# ── single-shot scenarios ────────────────────────────────────────────────────

def benign():
    payload, ua = g.benign()
    yield Event("Safe", payload, ua, g.random_client_ip())


def sqli():
    yield Event("SQL Injection", g.sql_injection(),
                random.choice(g.SAFE_USER_AGENTS), g.random_attacker_ip())


def xss():
    yield Event("XSS", g.xss(),
                random.choice(g.SAFE_USER_AGENTS), g.random_attacker_ip())


def path():
    yield Event("Path Traversal", g.path_traversal(),
                random.choice(g.SAFE_USER_AGENTS), g.random_attacker_ip())


def cmd():
    yield Event("Command Injection", g.command_injection(),
                random.choice(g.SAFE_USER_AGENTS), g.random_attacker_ip())


# ── burst scenarios ──────────────────────────────────────────────────────────

def rate_abuse(burst: int = 30):
    """One IP hammers /login fast. Past the backend's RATE_LIMIT this is logged
    as 'Brute Force / Rate Abuse' and the IP is auto-blocked."""
    ip = g.random_attacker_ip()
    for _ in range(max(1, burst)):
        yield Event("Rate Abuse", "POST /login username=admin&password=guess",
                    random.choice(g.SAFE_USER_AGENTS), ip, gap=0.0)


def port_scan(ports: int = 12):
    """One IP using a scanner user-agent probes many paths/ports in quick
    succession. The backend flags each as 'Suspicious User-Agent'."""
    ip = g.random_attacker_ip()
    ua = random.choice(g.SCANNER_USER_AGENTS)
    probes = random.sample(g.SCAN_PATHS, min(max(1, ports), len(g.SCAN_PATHS)))
    for probe in probes:
        yield Event("Port Scan", probe, ua, ip, gap=0.05)


# ── registry + mixed-stream weighting ────────────────────────────────────────

SCENARIOS = {
    "benign": benign,
    "sqli": sqli,
    "xss": xss,
    "path": path,
    "cmd": cmd,
    "rate_abuse": rate_abuse,
    "port_scan": port_scan,
}

# (name, weight) for the default mixed stream — mostly benign, occasional bursts.
MIXED_WEIGHTS = [
    ("benign", 0.60),
    ("sqli", 0.10),
    ("xss", 0.08),
    ("path", 0.07),
    ("cmd", 0.07),
    ("rate_abuse", 0.04),
    ("port_scan", 0.04),
]


def pick_mixed() -> str:
    names = [n for n, _ in MIXED_WEIGHTS]
    weights = [w for _, w in MIXED_WEIGHTS]
    return random.choices(names, weights=weights, k=1)[0]
