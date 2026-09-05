import asyncio
import time
from collections import deque
from contextlib import asynccontextmanager


class AsyncRateLimiter:
    """Bound concurrent provider calls and requests in a rolling time window."""

    def __init__(self, max_concurrency: int, requests_per_minute: int) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._requests_per_minute = requests_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def limit(self):
        started = time.perf_counter()
        await self._semaphore.acquire()
        try:
            async with self._lock:
                while True:
                    now = time.monotonic()
                    while self._timestamps and now - self._timestamps[0] >= 60:
                        self._timestamps.popleft()
                    if len(self._timestamps) < self._requests_per_minute:
                        self._timestamps.append(now)
                        break
                    await asyncio.sleep(60 - (now - self._timestamps[0]))
            yield (time.perf_counter() - started) * 1000
        finally:
            self._semaphore.release()
