import atexit
import threading

import httpx

_LIMITS = httpx.Limits(
    max_connections=50,
    max_keepalive_connections=20,
    keepalive_expiry=30.0,
)
_lock = threading.Lock()
_sync_client: httpx.Client | None = None
_async_client: httpx.AsyncClient | None = None


def shared_http_client() -> httpx.Client:
    """Return the process-wide synchronous HTTP connection pool."""
    global _sync_client
    if _sync_client is None or _sync_client.is_closed:
        with _lock:
            if _sync_client is None or _sync_client.is_closed:
                _sync_client = httpx.Client(limits=_LIMITS)
    return _sync_client


def shared_async_http_client() -> httpx.AsyncClient:
    """Return the process-wide asynchronous HTTP connection pool."""
    global _async_client
    if _async_client is None or _async_client.is_closed:
        with _lock:
            if _async_client is None or _async_client.is_closed:
                _async_client = httpx.AsyncClient(limits=_LIMITS)
    return _async_client


def close_sync_http_client() -> None:
    global _sync_client
    if _sync_client is not None and not _sync_client.is_closed:
        _sync_client.close()
    _sync_client = None


async def close_http_clients() -> None:
    """Release shared pools during application shutdown."""
    global _async_client
    close_sync_http_client()
    if _async_client is not None and not _async_client.is_closed:
        await _async_client.aclose()
    _async_client = None


atexit.register(close_sync_http_client)
