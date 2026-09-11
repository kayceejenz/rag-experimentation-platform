import unittest

from pydantic import ValidationError

from src.core.settings import Settings


class ProductionSettingsTests(unittest.TestCase):
    def production_settings(self, **overrides):
        values = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://ragapp:secret@database/ragapp",
            "JWT_SECRET": "a-unique-production-secret-with-32-chars",
            "CORS_ORIGINS": "https://rag.example.com",
            "REGISTRATION_INVITATION_CODE": "recruiter-access-code-2026",
        }
        values.update(overrides)
        return Settings(_env_file=None, **values)

    def test_secure_production_configuration_is_accepted(self):
        settings = self.production_settings()

        self.assertEqual(settings.app_env, "production")

    def test_database_is_required_in_production(self):
        with self.assertRaisesRegex(ValidationError, "DATABASE_URL is required"):
            self.production_settings(DATABASE_URL=None)

    def test_development_jwt_secret_is_rejected_in_production(self):
        with self.assertRaisesRegex(ValidationError, "JWT_SECRET must be"):
            self.production_settings(JWT_SECRET="local-jwt-secret-change-me")

    def test_short_jwt_secret_is_rejected_in_production(self):
        with self.assertRaisesRegex(ValidationError, "JWT_SECRET must be"):
            self.production_settings(JWT_SECRET="too-short")

    def test_wildcard_cors_is_rejected_in_production(self):
        with self.assertRaisesRegex(ValidationError, "cannot contain a wildcard"):
            self.production_settings(CORS_ORIGINS="*")

    def test_invitation_code_is_required_in_production(self):
        with self.assertRaisesRegex(
            ValidationError, "REGISTRATION_INVITATION_CODE must contain"
        ):
            self.production_settings(REGISTRATION_INVITATION_CODE=None)

    def test_partial_r2_configuration_is_rejected(self):
        with self.assertRaisesRegex(
            ValidationError, "R2 storage configuration is incomplete"
        ):
            self.production_settings(R2_API="https://storage.example.com")

    def test_development_defaults_remain_available(self):
        settings = Settings(_env_file=None)

        self.assertEqual(settings.app_env, "development")
        self.assertEqual(settings.jwt_secret, "local-jwt-secret-change-me")


if __name__ == "__main__":
    unittest.main()
