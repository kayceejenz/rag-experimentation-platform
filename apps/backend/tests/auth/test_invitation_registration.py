import unittest
from unittest.mock import Mock

from modules.auth.models.error_model import InvalidInvitationCodeError
from modules.auth.services.auth_service import AuthenticationService


class InvitationRegistrationTests(unittest.TestCase):
    def service(self, invitation_code: str | None):
        accounts = Mock()
        hasher = Mock()
        hasher.hash.side_effect = lambda value: f"hashed:{value}"
        service = AuthenticationService(
            accounts=accounts,
            hasher=hasher,
            recorder=Mock(),
            access_tokens=Mock(),
            refresh_tokens=Mock(),
            account_writer=accounts,
            registration_invitation_code=invitation_code,
        )
        return service, accounts

    def test_invalid_invitation_is_rejected_before_account_lookup(self):
        service, accounts = self.service("recruiter-access-code")

        with self.assertRaises(InvalidInvitationCodeError):
            service.register("candidate@example.com", "long-enough-password", None, "wrong")

        accounts.find_by_email.assert_not_called()
        accounts.create.assert_not_called()

    def test_valid_invitation_allows_registration(self):
        service, accounts = self.service("recruiter-access-code")
        accounts.find_by_email.return_value = None
        accounts.create.return_value.user = Mock()

        result = service.register(
            "candidate@example.com",
            "long-enough-password",
            "Candidate",
            "recruiter-access-code",
        )

        self.assertIs(result, accounts.create.return_value.user)
        accounts.create.assert_called_once()

    def test_development_registration_remains_open_without_configured_code(self):
        service, accounts = self.service(None)
        accounts.find_by_email.return_value = None
        accounts.create.return_value.user = Mock()

        service.register("developer@example.com", "long-enough-password", None)

        accounts.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
