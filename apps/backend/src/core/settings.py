from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "apps/backend/.env"), extra="ignore", populate_by_name=True
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    database_pool_min_size: int = Field(default=1, alias="DATABASE_POOL_MIN_SIZE", ge=0)
    database_pool_max_size: int = Field(
        default=10, alias="DATABASE_POOL_MAX_SIZE", ge=1
    )
    database_pool_timeout_seconds: float = Field(
        default=10.0, alias="DATABASE_POOL_TIMEOUT_SECONDS", ge=1.0
    )
    app_env: str = Field(default="development", alias="APP_ENV")
    app_revision: str = Field(default="development", alias="APP_REVISION")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    jwt_secret: str = Field(default="local-jwt-secret-change-me", alias="JWT_SECRET")
    jwt_issuer: str = Field(default="ragapp", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="ragapp-api", alias="JWT_AUDIENCE")
    access_token_minutes: int = Field(default=15, alias="ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=30, alias="REFRESH_TOKEN_DAYS")
    registration_invitation_code: str | None = Field(
        default=None,
        alias="REGISTRATION_INVITATION_CODE",
        max_length=256,
    )
    registration_rate_limit: int = Field(
        default=5,
        alias="REGISTRATION_RATE_LIMIT",
        ge=1,
        le=100,
    )
    registration_rate_window_seconds: int = Field(
        default=3600,
        alias="REGISTRATION_RATE_WINDOW_SECONDS",
        ge=60,
        le=86400,
    )
    login_rate_limit: int = Field(
        default=10,
        alias="LOGIN_RATE_LIMIT",
        ge=1,
        le=1000,
    )
    login_rate_window_seconds: int = Field(
        default=900,
        alias="LOGIN_RATE_WINDOW_SECONDS",
        ge=60,
        le=86400,
    )
    source_storage_dir: str = Field(
        default="storage/sources", alias="SOURCE_STORAGE_DIR"
    )
    worker_poll_interval_seconds: float = Field(
        default=30.0,
        alias="WORKER_POLL_INTERVAL_SECONDS",
        ge=5.0,
        le=300.0,
    )
    job_lease_seconds: int = Field(
        default=1200, alias="JOB_LEASE_SECONDS", ge=60, le=3600
    )
    unstructured_api_key: str | None = Field(default=None, alias="UNSTRUCTURED_API_KEY")
    unstructured_api_url: str | None = Field(default=None, alias="UNSTRUCTURED_API_URL")
    unstructured_strategy: str = Field(default="auto", alias="UNSTRUCTURED_STRATEGY")
    unstructured_pdf_strategy: str = Field(
        default="hi_res", alias="UNSTRUCTURED_PDF_STRATEGY"
    )
    unstructured_ocr_languages: str = Field(
        default="eng", alias="UNSTRUCTURED_OCR_LANGUAGES"
    )
    unstructured_poll_interval_seconds: float = Field(
        default=5.0, alias="UNSTRUCTURED_POLL_INTERVAL_SECONDS", ge=1.0, le=60.0
    )
    unstructured_job_timeout_seconds: float = Field(
        default=900.0, alias="UNSTRUCTURED_JOB_TIMEOUT_SECONDS", ge=60.0, le=3600.0
    )
    retrieval_candidate_limit: int = Field(
        default=16, alias="RETRIEVAL_CANDIDATE_LIMIT", ge=5, le=50
    )
    retrieval_result_limit: int = Field(
        default=5, alias="RETRIEVAL_RESULT_LIMIT", ge=1, le=12
    )
    retrieval_min_score: float = Field(
        default=0.50, alias="RETRIEVAL_MIN_SCORE", ge=0, le=1
    )
    experiment_max_context_chars: int = Field(
        default=24_000, alias="EXPERIMENT_MAX_CONTEXT_CHARS", ge=1_000, le=200_000
    )
    experiment_variant_concurrency: int = Field(
        default=2, alias="EXPERIMENT_VARIANT_CONCURRENCY", ge=1, le=16
    )
    experiment_case_concurrency: int = Field(
        default=4, alias="EXPERIMENT_CASE_CONCURRENCY", ge=1, le=32
    )
    experiment_evaluator_concurrency: int = Field(
        default=2, alias="EXPERIMENT_EVALUATOR_CONCURRENCY", ge=1, le=16
    )
    experiment_provider_max_concurrency: int = Field(
        default=4, alias="EXPERIMENT_PROVIDER_MAX_CONCURRENCY", ge=1, le=32
    )
    experiment_provider_requests_per_minute: int = Field(
        default=60, alias="EXPERIMENT_PROVIDER_REQUESTS_PER_MINUTE", ge=1, le=10_000
    )
    experiment_run_lease_seconds: int = Field(
        default=900, alias="EXPERIMENT_RUN_LEASE_SECONDS", ge=60, le=7_200
    )
    chat_max_output_tokens: int = Field(
        default=500, alias="CHAT_MAX_OUTPUT_TOKENS", ge=100, le=2000
    )
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    embedding_provider: str = Field(default="ollama", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(
        default=768, alias="EMBEDDING_DIMENSIONS", ge=128, le=3072
    )
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_batch_size: int = Field(
        default=100, alias="EMBEDDING_BATCH_SIZE", ge=1, le=100
    )
    gemini_api_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="GEMINI_API_URL",
    )
    gemini_thinking_level: str = Field(default="low", alias="GEMINI_THINKING_LEVEL")
    r2_account_id: str | None = Field(default=None, alias="R2_ACCOUNT_ID")
    r2_api: str | None = Field(default=None, alias="R2_API")
    r2_bucket_name: str | None = Field(default=None, alias="R2_BUCKET_NAME")
    r2_access_key_id: str | None = Field(default=None, alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str | None = Field(default=None, alias="R2_SECRET_ACCESS_KEY")

    @model_validator(mode="after")
    def validate_production_configuration(self) -> Self:
        if self.app_env.strip().lower() != "production":
            return self

        errors: list[str] = []
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        if (
            len(self.jwt_secret.strip()) < 32
            or self.jwt_secret == "local-jwt-secret-change-me"
        ):
            errors.append("JWT_SECRET must be a unique secret of at least 32 characters")
        if (
            not self.registration_invitation_code
            or len(self.registration_invitation_code.strip()) < 16
        ):
            errors.append(
                "REGISTRATION_INVITATION_CODE must contain at least 16 characters"
            )
        if not self.allowed_origins:
            errors.append("CORS_ORIGINS must contain at least one trusted origin")
        if "*" in self.allowed_origins:
            errors.append("CORS_ORIGINS cannot contain a wildcard")

        configured_r2_values = {
            "R2_API": self.r2_api,
            "R2_BUCKET_NAME": self.r2_bucket_name,
            "R2_ACCESS_KEY_ID": self.r2_access_key_id,
            "R2_SECRET_ACCESS_KEY": self.r2_secret_access_key,
        }
        if any(configured_r2_values.values()) and not all(configured_r2_values.values()):
            missing = [
                name for name, value in configured_r2_values.items() if not value
            ]
            errors.append(f"R2 storage configuration is incomplete: {', '.join(missing)}")

        if errors:
            raise ValueError("Invalid production configuration: " + "; ".join(errors))
        return self

    @property
    def has_database(self) -> bool:
        return bool(self.database_url)

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def ocr_languages(self) -> list[str]:
        return [
            language.strip() for language in self.unstructured_ocr_languages.split(",")
        ]

    @property
    def effective_embedding_api_key(self) -> str | None:
        return self.embedding_api_key or self.llm_api_key
