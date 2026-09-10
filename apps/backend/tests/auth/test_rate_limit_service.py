import unittest
from dataclasses import dataclass

from modules.auth.models.error_model import AuthRateLimitExceededError
from modules.auth.services.rate_limit_service import AuthRateLimiter


@dataclass
class Usage:
    attempts: int
    retry_after_seconds: int = 60


class Repository:
    def __init__(self):
        self.attempts = 0
        self.calls = []

    def consume(self, action, client_key, window_seconds):
        self.attempts += 1
        self.calls.append((action, client_key, window_seconds))
        return Usage(self.attempts)


class AuthRateLimiterTests(unittest.TestCase):
    def setUp(self):
        self.repository = Repository()
        self.limiter = AuthRateLimiter(
            self.repository,
            "test-secret",
            registration_limit=2,
            registration_window_seconds=3600,
            login_limit=3,
            login_window_seconds=900,
        )

    def test_request_within_policy_is_allowed(self):
        self.limiter.check("register", "192.0.2.1")
        self.limiter.check("register", "192.0.2.1")

        self.assertEqual(len(self.repository.calls), 2)

    def test_request_above_policy_is_rejected_with_retry_time(self):
        self.limiter.check("register", "192.0.2.1")
        self.limiter.check("register", "192.0.2.1")

        with self.assertRaises(AuthRateLimitExceededError) as raised:
            self.limiter.check("register", "192.0.2.1")

        self.assertEqual(raised.exception.retry_after_seconds, 60)

    def test_client_identifier_is_not_persisted_in_plain_text(self):
        self.limiter.check("login", "192.0.2.1")

        action, client_key, window_seconds = self.repository.calls[0]
        self.assertEqual(action, "login")
        self.assertNotEqual(client_key, "192.0.2.1")
        self.assertEqual(len(client_key), 64)
        self.assertEqual(window_seconds, 900)


if __name__ == "__main__":
    unittest.main()
