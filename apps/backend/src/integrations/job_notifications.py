import asyncio
import logging

from psycopg import AsyncConnection, InterfaceError, OperationalError


WORKER_JOBS_CHANNEL = "ragapp_worker_jobs"

logger = logging.getLogger(__name__)


def notify_worker(connection, workload: str) -> None:
    """Wake workers after the transaction that queued work commits."""
    connection.execute(
        "select pg_notify(%s,%s)",
        (WORKER_JOBS_CHANNEL, workload),
    )


class JobNotificationListener:
    """Dedicated PostgreSQL listener used as a non-durable worker wake-up signal."""

    def __init__(self, database_url: str, reconnect_delay_seconds: float = 5.0) -> None:
        self.database_url = database_url
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self._connection: AsyncConnection | None = None

    async def open(self) -> bool:
        if self._connection is not None and not self._connection.closed:
            return True
        try:
            connection = await AsyncConnection.connect(
                self.database_url,
                autocommit=True,
            )
            self._connection = connection
            await connection.execute(f"listen {WORKER_JOBS_CHANNEL}")
            return True
        except (InterfaceError, OperationalError, OSError):
            logger.warning("Could not open worker notification listener", exc_info=True)
            await self.close()
            return False

    async def wait(self, fallback_seconds: float) -> bool:
        """Return True for a notification and False for timeout or disconnection."""
        try:
            if not await self.open():
                await asyncio.sleep(
                    min(fallback_seconds, self.reconnect_delay_seconds)
                )
                return False
            assert self._connection is not None
            async for _notification in self._connection.notifies(
                timeout=fallback_seconds,
                stop_after=1,
            ):
                return True
            return False
        except (InterfaceError, OperationalError, OSError):
            logger.warning("Worker notification listener disconnected", exc_info=True)
            await self.close()
            await asyncio.sleep(min(fallback_seconds, self.reconnect_delay_seconds))
            return False

    async def close(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None and not connection.closed:
            await connection.close()
