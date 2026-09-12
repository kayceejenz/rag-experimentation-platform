import unittest
from unittest.mock import AsyncMock, patch

from integrations.job_notifications import (
    JobNotificationListener,
    WORKER_JOBS_CHANNEL,
    notify_worker,
)


class SyncConnection:
    def __init__(self):
        self.calls = []

    def execute(self, statement, parameters):
        self.calls.append((statement, parameters))


class AsyncNotifications:
    def __init__(self, values):
        self.values = values

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.values:
            raise StopAsyncIteration
        return self.values.pop(0)


class AsyncConnection:
    def __init__(self, notifications=()):
        self.closed = False
        self.execute = AsyncMock()
        self.notifications = list(notifications)

    def notifies(self, **_kwargs):
        return AsyncNotifications(self.notifications)

    async def close(self):
        self.closed = True


class NotificationTests(unittest.TestCase):
    def test_notify_uses_one_shared_channel_and_small_workload_payload(self):
        connection = SyncConnection()

        notify_worker(connection, "experiment")

        self.assertEqual(
            [("select pg_notify(%s,%s)", (WORKER_JOBS_CHANNEL, "experiment"))],
            connection.calls,
        )


class ListenerTests(unittest.IsolatedAsyncioTestCase):
    async def test_listener_subscribes_and_reports_a_notification(self):
        connection = AsyncConnection([object()])
        listener = JobNotificationListener("postgresql://test")

        with patch(
            "integrations.job_notifications.AsyncConnection.connect",
            new=AsyncMock(return_value=connection),
        ) as connect:
            received = await listener.wait(30)

        self.assertTrue(received)
        connect.assert_awaited_once_with("postgresql://test", autocommit=True)
        connection.execute.assert_awaited_once_with(
            f"listen {WORKER_JOBS_CHANNEL}"
        )

    async def test_listener_returns_false_when_fallback_time_expires(self):
        connection = AsyncConnection()
        listener = JobNotificationListener("postgresql://test")

        with patch(
            "integrations.job_notifications.AsyncConnection.connect",
            new=AsyncMock(return_value=connection),
        ):
            received = await listener.wait(30)

        self.assertFalse(received)

    async def test_listener_failure_does_not_replace_fallback_polling(self):
        listener = JobNotificationListener(
            "postgresql://test",
            reconnect_delay_seconds=0,
        )

        with patch(
            "integrations.job_notifications.AsyncConnection.connect",
            new=AsyncMock(side_effect=OSError("database unavailable")),
        ), patch("integrations.job_notifications.logger.warning"):
            received = await listener.wait(30)

        self.assertFalse(received)


if __name__ == "__main__":
    unittest.main()
