from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "apps/backend/.env"), extra="ignore", populate_by_name=True
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    jwt_secret: str = Field(default="local-jwt-secret-change-me", alias="JWT_SECRET")
    jwt_issuer: str = Field(default="ragapp", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="ragapp-api", alias="JWT_AUDIENCE")
    access_token_minutes: int = Field(default=15, alias="ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=30, alias="REFRESH_TOKEN_DAYS")
    source_storage_dir: str = Field(default="storage/sources", alias="SOURCE_STORAGE_DIR")
    worker_poll_interval_seconds: float = Field(default=5.0, alias="WORKER_POLL_INTERVAL_SECONDS")
    job_lease_seconds: int = Field(default=1200, alias="JOB_LEASE_SECONDS", ge=60, le=3600)
    unstructured_api_key: str | None = Field(default=None, alias="UNSTRUCTURED_API_KEY")
    unstructured_api_url: str | None = Field(default=None, alias="UNSTRUCTURED_API_URL")
    unstructured_strategy: str = Field(default="auto", alias="UNSTRUCTURED_STRATEGY")
    unstructured_pdf_strategy: str = Field(default="hi_res", alias="UNSTRUCTURED_PDF_STRATEGY")
    unstructured_ocr_languages: str = Field(default="eng", alias="UNSTRUCTURED_OCR_LANGUAGES")
    unstructured_poll_interval_seconds: float = Field(
        default=5.0, alias="UNSTRUCTURED_POLL_INTERVAL_SECONDS", ge=1.0, le=60.0
    )
    unstructured_job_timeout_seconds: float = Field(
        default=900.0, alias="UNSTRUCTURED_JOB_TIMEOUT_SECONDS", ge=60.0, le=3600.0
    )
    retrieval_candidate_limit: int = Field(default=16, alias="RETRIEVAL_CANDIDATE_LIMIT", ge=5, le=50)
    retrieval_result_limit: int = Field(default=5, alias="RETRIEVAL_RESULT_LIMIT", ge=1, le=12)
    retrieval_min_score: float = Field(default=0.50, alias="RETRIEVAL_MIN_SCORE", ge=0, le=1)
    chat_max_output_tokens: int = Field(default=500, alias="CHAT_MAX_OUTPUT_TOKENS", ge=100, le=2000)
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    embedding_provider: str = Field(default="ollama", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=768, alias="EMBEDDING_DIMENSIONS", ge=128, le=3072)
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_batch_size: int = Field(default=100, alias="EMBEDDING_BATCH_SIZE", ge=1, le=100)
    gemini_api_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta", alias="GEMINI_API_URL"
    )
    gemini_thinking_level: str = Field(default="low", alias="GEMINI_THINKING_LEVEL")
    r2_account_id: str | None = Field(default=None, alias="R2_ACCOUNT_ID")
    r2_api: str | None = Field(default=None, alias="R2_API")
    r2_bucket_name: str | None = Field(default=None, alias="R2_BUCKET_NAME")
    r2_access_key_id: str | None = Field(default=None, alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str | None = Field(default=None, alias="R2_SECRET_ACCESS_KEY")

    @property
    def has_database(self) -> bool:
        return bool(self.database_url)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ocr_languages(self) -> list[str]:
        return [language.strip() for language in self.unstructured_ocr_languages.split(",")]

    @property
    def effective_embedding_api_key(self) -> str | None:
        return self.embedding_api_key or self.llm_api_key
