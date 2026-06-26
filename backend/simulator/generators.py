"""Synthetic identity + payload generators for the demo simulator.

All attack strings here are short, textbook *detection-test* tokens used to
trigger ACSTD's own signatures — synthetic demo input, not working exploits.
"""
import random

# ── identities ───────────────────────────────────────────────────────────────

SAFE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) Mobile/15E148",
]

# Tool names the backend's signature list recognises (-> Suspicious User-Agent).
SCANNER_USER_AGENTS = [
    "nmap/7.94", "masscan/1.3.2", "zgrab/0.x", "Nikto/2.1.6",
    "gobuster/3.6", "dirbuster/1.0", "sqlmap/1.7",
]

# Stable pool for ordinary clients (so the dashboard shows familiar IPs).
CLIENT_IPS = [
    "203.0.113.5", "198.51.100.12", "10.0.0.87", "192.168.1.45",
    "45.33.32.156", "185.220.101.3", "91.108.4.11", "172.16.0.99",
]


def random_client_ip() -> str:
    return random.choice(CLIENT_IPS)


def random_attacker_ip() -> str:
    """A fresh external-looking IP, so each attack burst is distinct."""
    return f"{random.choice([45, 185, 91, 103, 193])}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


# ── benign traffic ───────────────────────────────────────────────────────────

SAFE_PAYLOADS = [
    "GET /index.html", "GET /about", "GET /products?page=2",
    "POST /login username=alice&password=hunter2", "GET /api/users/42",
    "GET /static/logo.png", "POST /contact name=Bob&message=Hello",
    "GET /search?q=shoes", "GET /favicon.ico", "POST /api/cart item_id=7&qty=1",
    "GET /dashboard", "GET /api/status",
]


def benign() -> tuple[str, str]:
    return random.choice(SAFE_PAYLOADS), random.choice(SAFE_USER_AGENTS)


# ── attack payload pools (synthetic, textbook) ───────────────────────────────

_SQLI = [
    "' OR '1'='1' --", "1; DROP TABLE users--",
    "' UNION SELECT username,password FROM users--",
    "admin'--", "' OR 1=1#", "1' AND SLEEP(5)-- -",
]
_XSS = [
    "<script>document.cookie</script>", "<img src=x onerror=alert('xss')>",
    "javascript:alert(1)", "<svg onload=alert(1)>",
    "\"><script>alert(document.domain)</script>",
]
_PATH = [
    "../../etc/passwd", "../../../windows/system32/config/sam",
    "%2e%2e%2f%2e%2e%2fetc/shadow", "....//....//etc/passwd",
    "/var/www/../../etc/hosts",
]
# Signature precedence is SQLi > XSS > Path Traversal > Command Injection, so a
# Command Injection payload must avoid tokens an earlier rule would claim:
#  - no ';' or quote  (SQLi rule),
#  - no '/etc/passwd' etc. literal paths  (Path Traversal rule),
#  - command adjacent to the separator, no space  (Command Injection rule).
# Tame reconnaissance tokens, not working exploit commands.
_CMD = [
    "|whoami", "&&ls -la /", "$(id)", "`id`",
    "&&whoami", "$(whoami)",
]


def sql_injection() -> str:     return random.choice(_SQLI)
def xss() -> str:               return random.choice(_XSS)
def path_traversal() -> str:    return random.choice(_PATH)
def command_injection() -> str: return random.choice(_CMD)


# ── port-scan probe targets ──────────────────────────────────────────────────

SCAN_PATHS = [
    "GET /:21", "GET /:22", "GET /:80", "GET /:443", "GET /:3306", "GET /:6379",
    "GET /admin", "GET /.git/config", "GET /.env", "GET /phpmyadmin",
    "GET /wp-login.php", "GET /server-status",
]
