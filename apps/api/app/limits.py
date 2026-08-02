"""Small single-process limit for the public demo lookup route."""

from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic


class FixedWindowRateLimiter:
    """Bounds local/demo traffic; production must also enforce limits at the edge."""

    def __init__(self, requests_per_minute: int) -> None:
        self._limit = requests_per_minute
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, client_key: str) -> bool:
        now = monotonic()
        cutoff = now - 60
        history = self._requests[client_key]
        while history and history[0] < cutoff:
            history.popleft()
        if len(history) >= self._limit:
            return False
        history.append(now)
        return True

