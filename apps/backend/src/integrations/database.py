import threading
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from psycopg import AsyncConnection, Connection
from psycopg.rows import RowFactory, tuple_row
from psycopg_pool import AsyncConnectionPool, ConnectionPool

_lock = threading.Lock()
_sync_pools: dict[str, ConnectionPool] = {}
_async_pools: dict[str, AsyncConnectionPool] = {}


def _pool_kwargs(min_size: int, max_size: int, timeout: float) -> dict:
    return {
        "min_size": min_size,
        "max_size": max_size,
        "timeout": timeout,
        "max_lifetime": 1800.0,
        "max_idle": 300.0,
        "reconnect_timeout": 30.0,
        "kwargs": {"row_factory": tuple_row},
    }


def configure_database_pools(min_size: int, max_size: int, timeout: float) -> None:
    """Configure pool defaults before the first database checkout."""
    if min_size > max_size:
        raise ValueError("DATABASE_POOL_MIN_SIZE cannot exceed DATABASE_POOL_MAX_SIZE")
    database_pool.min_size = min_size
    database_pool.max_size = max_size
    database_pool.timeout = timeout


class _DatabasePoolConfiguration:
    min_size = 1
    max_size = 10
    timeout = 10.0


database_pool = _DatabasePoolConfiguration()


def _sync_pool(database_url: str) -> ConnectionPool:
    with _lock:
        pool = _sync_pools.get(database_url)
        if pool is None:
            pool = ConnectionPool(
                database_url,
                **_pool_kwargs(
                    database_pool.min_size,
                    database_pool.max_size,
                    database_pool.timeout,
                ),
            )
            _sync_pools[database_url] = pool
        return pool


def _async_pool(database_url: str) -> AsyncConnectionPool:
    with _lock:
        pool = _async_pools.get(database_url)
        if pool is None:
            pool = AsyncConnectionPool(
                database_url,
                open=False,
                **_pool_kwargs(
                    database_pool.min_size,
                    database_pool.max_size,
                    database_pool.timeout,
                ),
            )
            _async_pools[database_url] = pool
        return pool


@contextmanager
def db_connection(
    database_url: str, *, row_factory: RowFactory | None = None
) -> Iterator[Connection]:
    with _sync_pool(database_url).connection() as connection:
        connection.row_factory = row_factory or tuple_row
        yield connection


@asynccontextmanager
async def async_db_connection(
    database_url: str, *, row_factory: RowFactory | None = None
) -> AsyncIterator[AsyncConnection]:
    pool = _async_pool(database_url)
    if pool.closed:
        await pool.open(wait=True)
    async with pool.connection() as connection:
        connection.row_factory = row_factory or tuple_row
        yield connection


async def open_database_pools(database_url: str) -> None:
    """Open and validate both pools before accepting API traffic."""
    sync_pool = _sync_pool(database_url)
    sync_pool.wait()
    async_pool = _async_pool(database_url)
    if async_pool.closed:
        await async_pool.open(wait=True)


async def close_database_pools() -> None:
    with _lock:
        sync_pools = list(_sync_pools.values())
        async_pools = list(_async_pools.values())
        _sync_pools.clear()
        _async_pools.clear()
    for pool in sync_pools:
        pool.close()
    for pool in async_pools:
        await pool.close()
