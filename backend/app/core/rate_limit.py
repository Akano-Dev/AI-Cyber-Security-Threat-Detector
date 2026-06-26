"""Sliding-window rate limiter (in-memory).

Phase 5 replaces the backing store with Redis so limits are shared across workers.
"""
from collections import defaultdict, deque
from datetime import datetime, timezone

from app.config import settings


class RateLimiter:
    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)

    def is_exceeded(self, ip: str) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        dq = self._hits[ip]
        while dq and dq[0] < now - settings.rate_window:
            dq.popleft()
        dq.append(now)
        return len(dq) > settings.rate_limit


rate_limiter = RateLimiter()
