"""HTTP client that posts synthetic payloads to ACSTD's /analyze endpoint.

Dependency-free (urllib only) so the simulator runs anywhere Python does,
matching the original script's portability.
"""
import json
import urllib.error
import urllib.request


class AnalyzeClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1", timeout: float = 5.0):
        self.analyze_url = base_url.rstrip("/") + "/analyze"
        self.timeout = timeout

    def send(self, payload: str, user_agent: str = "unknown", source_ip: str = "0.0.0.0") -> dict:
        """POST one payload; return the parsed JSON verdict (or {'error': ...})."""
        body = json.dumps({
            "source_ip": source_ip,
            "payload": payload,
            "user_agent": user_agent,
        }).encode()
        req = urllib.request.Request(
            self.analyze_url, data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.URLError as exc:
            return {"error": str(exc)}
        except Exception as exc:  # malformed response, etc. — never crash the run
            return {"error": str(exc)}
