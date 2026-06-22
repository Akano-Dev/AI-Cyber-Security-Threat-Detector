import re

PAYLOAD_RULES = [
    {
        "threat_type": "SQL Injection",
        "severity": "high",
        "pattern": re.compile(
            r"('|--|;|/\*|\*/|xp_|union\s+select|select\s+.+from|insert\s+into|drop\s+table|or\s+'1'\s*=\s*'1)",
            re.IGNORECASE,
        ),
    },
    {
        "threat_type": "XSS",
        "severity": "medium",
        "pattern": re.compile(
            r"(<script|</script|javascript:|onerror\s*=|onload\s*=|<img\s|<iframe|alert\s*\(|document\.cookie)",
            re.IGNORECASE,
        ),
    },
    {
        "threat_type": "Path Traversal",
        "severity": "high",
        "pattern": re.compile(
            r"(\.\./|\.\.\\|%2e%2e%2f|%252e%252e|/etc/passwd|/etc/shadow|windows/system32)",
            re.IGNORECASE,
        ),
    },
    {
        "threat_type": "Command Injection",
        "severity": "high",
        "pattern": re.compile(
            r"(;|\||&&|\$\(|`)(ls|cat|rm|wget|curl|bash|sh|cmd|powershell|whoami|id|nc\s)",
            re.IGNORECASE,
        ),
    },
]

SUSPICIOUS_USER_AGENTS = re.compile(
    r"(sqlmap|nikto|nmap|masscan|zgrab|dirbuster|gobuster|hydra|medusa|burpsuite|metasploit|nessus|acunetix)",
    re.IGNORECASE,
)


def analyze(payload: str, user_agent: str) -> dict | None:
    """Return {threat_type, severity} if a threat is detected, else None."""
    for rule in PAYLOAD_RULES:
        if rule["pattern"].search(payload):
            return {"threat_type": rule["threat_type"], "severity": rule["severity"]}

    if SUSPICIOUS_USER_AGENTS.search(user_agent):
        return {"threat_type": "Suspicious User-Agent", "severity": "low"}

    return None
