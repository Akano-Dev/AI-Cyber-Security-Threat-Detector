"""In-memory runtime metrics (process-local).

Phase 5 note: like the rate-limiter and blocklist, these counters are per-worker.
A multi-worker deployment would export them to Prometheus / a shared store.
"""
import time
from collections import Counter


class Metrics:
    def __init__(self):
        self._start = time.monotonic()
        self.requests_total = 0
        self.responses_by_class: Counter = Counter()  # "2xx", "4xx", ...
        self._response_ms_sum = 0.0

    def observe(self, status_code: int, elapsed_ms: float) -> None:
        self.requests_total += 1
        self.responses_by_class[f"{status_code // 100}xx"] += 1
        self._response_ms_sum += elapsed_ms

    @property
    def uptime_seconds(self) -> float:
        return round(time.monotonic() - self._start, 1)

    @property
    def avg_response_ms(self) -> float:
        return round(self._response_ms_sum / self.requests_total, 2) if self.requests_total else 0.0


metrics = Metrics()
