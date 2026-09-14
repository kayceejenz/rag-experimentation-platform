from functools import lru_cache
from typing import Annotated

from core.settings import Settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from integrations.assistant_runtime import AssistantRuntimeFactory
from integrations.embeddings import GeminiEmbedder
from integrations.gemini_chat import GeminiChatModel
from integrations.retrieval_store import PgVectorKnowledgeSearch
from modules.assistants.repos.assistant_repository import AssistantRepository
from modules.assistants.services.assistant_service import AssistantService
from modules.auth.helpers.passwords import Argon2idPasswordHasher
from modules.auth.helpers.tokens import JwtAccessTokenIssuer
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.auth.models.error_model import InvalidAccessTokenError
from modules.auth.repos.rate_limit_repo import AuthRateLimitRepository
from modules.auth.repos.refresh_token_repo import RefreshTokenRepository
from modules.auth.repos.user_repo import UserRepository
from modules.auth.services.auth_service import AuthenticationService
from modules.auth.services.rate_limit_service import AuthRateLimiter
from modules.benchmarks.repos.benchmark_repository import BenchmarkRepository
from modules.benchmarks.services.benchmark_service import BenchmarkService
from modules.chats.repos.chat_repo import ChatRepository
from modules.chats.repos.message_repo import MessageRepository
from modules.chats.services.chat_service import ChatService
from modules.core.repos.lineage_repo import LineageRepository
from modules.core.repos.specification_repo import SpecificationRepository
from modules.core.services.lineage_service import LineageService
from modules.core.services.specification_service import SpecificationService
from modules.experiments.repos.experiment_repository import ExperimentRepository
from modules.experiments.repos.run_repository import ExperimentRunRepository
from modules.experiments.services.experiment_service import ExperimentService
from modules.indexes.repos.index_repository import IndexRepository
from modules.indexes.services.index_service import IndexService
from modules.ingestion.services.ingestion_specification import (
    IngestionSpecificationRegistry,
)
from modules.jobs.repos.job_repo import JobRepository
from modules.jobs.services.job_service import JobService
from modules.knowledge_bases.repos.knowledge_base_repo import KnowledgeBaseRepository
from modules.knowledge_bases.services.knowledge_base_service import KnowledgeBaseService
from modules.projects.repos.project_repo import ProjectRepository
from modules.projects.services.project_service import ProjectService
from modules.prompts.repos.prompt_repository import PromptRepository
from modules.prompts.services.prompt_service import PromptService
from modules.sources.repos.source_repo import SourceRepository
from modules.sources.services.source_service import SourceService

bearer = HTTPBearer(
    auto_error=False,
    scheme_name="JWT Bearer",
    bearerFormat="JWT",
    description="Paste the access token returned by POST /api/v1/auth/login.",
)


@lru_cache
def settings() -> Settings:
    return Settings()


@lru_cache
def auth_repository() -> UserRepository:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return UserRepository(settings().database_url)


@lru_cache
def token_issuer() -> JwtAccessTokenIssuer:
    c = settings()
    return JwtAccessTokenIssuer(
        c.jwt_secret, c.jwt_issuer, c.jwt_audience, c.access_token_minutes
    )


@lru_cache
def auth_service() -> AuthenticationService:
    c, repository = settings(), auth_repository()
    return AuthenticationService(
        repository,
        Argon2idPasswordHasher(),
        repository,
        token_issuer(),
        RefreshTokenRepository(repository),
        repository,
        c.refresh_token_days,
        c.registration_invitation_code,
    )


@lru_cache
def auth_rate_limiter() -> AuthRateLimiter:
    c = settings()
    if not c.database_url:
        raise RuntimeError("DATABASE_URL is required")
    return AuthRateLimiter(
        AuthRateLimitRepository(c.database_url),
        c.jwt_secret,
        c.registration_rate_limit,
        c.registration_rate_window_seconds,
        c.login_rate_limit,
        c.login_rate_window_seconds,
    )


@lru_cache
def project_service() -> ProjectService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return ProjectService(ProjectRepository(settings().database_url))


@lru_cache
def assistant_service() -> AssistantService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return AssistantService(
        AssistantRepository(settings().database_url), project_service()
    )


@lru_cache
def chat_service() -> ChatService:
    c = settings()
    if not c.database_url:
        raise RuntimeError("DATABASE_URL is required")

    if c.llm_provider.lower() != "gemini" or c.embedding_provider.lower() != "gemini":
        raise RuntimeError(
            "Chat currently requires Gemini for generation and embeddings"
        )

    api_key = c.llm_api_key or c.embedding_api_key
    embedding_key = c.embedding_api_key or c.llm_api_key
    if not api_key or not embedding_key or not c.llm_model:
        raise RuntimeError("LLM_API_KEY, EMBEDDING_API_KEY, and LLM_MODEL are required")

    embedder = GeminiEmbedder(
        embedding_key,
        c.embedding_model,
        c.embedding_dimensions,
        c.gemini_api_url,
        c.embedding_batch_size,
    )
    return ChatService(
        ChatRepository(c.database_url),
        project_service(),
        MessageRepository(c.database_url),
        PgVectorKnowledgeSearch(
            c.database_url,
            embedder,
            c.embedding_provider.lower(),
            c.embedding_model,
            c.retrieval_candidate_limit,
            c.retrieval_min_score,
        ),
        GeminiChatModel(
            api_key,
            c.llm_model,
            c.gemini_api_url,
            max_output_tokens=c.chat_max_output_tokens,
            thinking_level=c.gemini_thinking_level,
        ),
        assistant_service(),
        AssistantRuntimeFactory(c),
    )


@lru_cache
def knowledge_base_service() -> KnowledgeBaseService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return KnowledgeBaseService(KnowledgeBaseRepository(settings().database_url))


@lru_cache
def source_service() -> SourceService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return SourceService(
        SourceRepository(settings().database_url), settings().source_storage_dir
    )


@lru_cache
def job_service() -> JobService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return JobService(JobRepository(settings().database_url))


@lru_cache
def lineage_service() -> LineageService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return LineageService(
        LineageRepository(settings().database_url),
        project_service(),
    )


@lru_cache
def index_service() -> IndexService:
    c = settings()
    if not c.database_url:
        raise RuntimeError("DATABASE_URL is required")
    return IndexService(
        IndexRepository(c.database_url),
        SpecificationService(
            SpecificationRepository(c.database_url), IngestionSpecificationRegistry()
        ),
    )


@lru_cache
def prompt_service() -> PromptService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return PromptService(PromptRepository(settings().database_url))


@lru_cache
def benchmark_service() -> BenchmarkService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return BenchmarkService(BenchmarkRepository(settings().database_url))


@lru_cache
def experiment_service() -> ExperimentService:
    if not settings().database_url:
        raise RuntimeError("DATABASE_URL is required")
    return ExperimentService(
        ExperimentRepository(settings().database_url),
        ExperimentRunRepository(settings().database_url),
        settings().app_revision,
        [settings().llm_model],
    )


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthenticatedUser:
    error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Missing, invalid, or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise error

    try:
        return auth_service().authenticate_access_token(credentials.credentials)
    except InvalidAccessTokenError:
        raise error from None
