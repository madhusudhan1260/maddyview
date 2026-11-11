"""Small in-memory sliding-window rate limiter.

Adequate for a single-process, single-user deployment. A multi-process deployment
would need a shared store (e.g. Redis) — documented as a known limitation.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import RateLimitError


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


auth_limiter = SlidingWindowLimiter(get_settings().auth_rate_limit_per_minute)


def limit_auth(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    if not auth_limiter.hit(f"{client}:{request.url.path}"):
        raise RateLimitError("Too many attempts. Wait a minute and try again.")
