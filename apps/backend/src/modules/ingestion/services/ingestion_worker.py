import logging
import socket

from core.settings import Settings
from integrations.embeddings import GeminiEmbedder
from integrations.ingestion_store import (
    ChunkRepository,
    ElementAssetStore,
    ElementRepository,
)
from integrations.partitioner import UnstructuredPartitioner
from integrations.storage import cleanup_temp, resolve_file
from modules.core.models.execution_model import ExecutionStatus
from modules.core.repos.artifact_repo import ArtifactRepository
from modules.core.repos.execution_repo import ExecutionRepository
from modules.core.repos.specification_repo import SpecificationRepository
from modules.core.services.artifact_service import ArtifactService
from modules.core.services.execution_service import ExecutionService
from modules.core.services.specification_service import SpecificationService
from modules.ingestion.services.ingestion_service import IngestSource
from modules.ingestion.services.ingestion_specification import (
    IngestionSpecificationRegistry,
)
from modules.ingestion.services.ingestion_tracking_service import (
    IngestionTracker,
    installed_code_revision,
)
from modules.jobs.models.job_model import PipelineStage
from modules.jobs.repos.job_repo import JobRepository

logger = logging.getLogger(__name__)


def embedding_provider(config: Settings, embedding: dict | None = None):
    selected = embedding or {
        "provider": config.embedding_provider,
        "model": config.embedding_model,
        "dimensions": config.embedding_dimensions,
    }
    provider = str(selected["provider"]).lower()
    if provider == "gemini":
        if not config.effective_embedding_api_key:
            raise RuntimeError(
                "EMBEDDING_API_KEY or LLM_API_KEY is required for Gemini embeddings"
            )
        return GeminiEmbedder(
            api_key=config.effective_embedding_api_key,
            model=str(selected["model"]),
            dimensions=int(selected["dimensions"]),
            base_url=config.gemini_api_url,
            batch_size=config.embedding_batch_size,
        )
    raise RuntimeError(f"Unsupported embedding provider: {config.embedding_provider}")


def run_once(config: Settings) -> bool:
    if not config.database_url:
        return False
    queue = JobRepository(config.database_url, lease_seconds=config.job_lease_seconds)
    worker_id = socket.gethostname()
    job = queue.claim_next(worker_id)
    if not job:
        return False

    execution_repository = ExecutionRepository(config.database_url)
    tracker = IngestionTracker(
        ArtifactService(ArtifactRepository(config.database_url)),
        SpecificationService(
            SpecificationRepository(config.database_url),
            IngestionSpecificationRegistry(),
        ),
        ExecutionService(execution_repository),
        execution_repository,
        installed_code_revision(),
    )
    path = None
    temporary = False
    execution = None
    try:
        specification = (
            SpecificationRepository(config.database_url).get(
                job.specification_id, job.project_id
            )
            if job.specification_id
            else None
        )
        selected = specification.configuration if specification else None
        recovered = tracker.recover_previous_attempt(job)
        if recovered is not None:
            queue.complete(job, recovered.element_count, recovered.chunk_count)
            return True
        execution = tracker.begin(job, config, worker_id, specification)
        if execution.status is ExecutionStatus.COMPLETED:
            summary = execution.result_summary or {}
            queue.complete(
                job,
                int(summary["element_count"]),
                int(summary["chunk_count"]),
            )
            return True
        if execution.status is not ExecutionStatus.RUNNING:
            raise RuntimeError(
                f"Ingestion execution cannot continue from {execution.status.value}"
            )
        queue.renew_lease(job.id)
        embedding = selected["embedding"] if selected else None
        chunks = ChunkRepository(
            config.database_url,
            str(embedding["provider"]).lower()
            if embedding
            else config.embedding_provider.lower(),
            str(embedding["model"]) if embedding else config.embedding_model,
        )
        if job.stage is PipelineStage.CHUNK:
            if not config.unstructured_api_key:
                raise RuntimeError("UNSTRUCTURED_API_KEY is required for chunking")
            path, temporary = resolve_file(job.storage_key, config.source_storage_dir)
            ingestion = IngestSource(
                UnstructuredPartitioner(
                    config.unstructured_api_key,
                    config.unstructured_api_url,
                    config.unstructured_strategy,
                    config.unstructured_pdf_strategy,
                    config.ocr_languages,
                    config.unstructured_poll_interval_seconds,
                    config.unstructured_job_timeout_seconds,
                    chunking_strategy=str(selected["chunking"]["strategy"])
                    if selected
                    else "by_title",
                ),
                ElementRepository(config.database_url),
                chunks,
                ElementAssetStore(config.source_storage_dir),
            )
            element_count, chunk_count = ingestion.execute_chunking(
                job.project_id,
                job.source_id,
                job.source_version_id,
                job.knowledge_base_id,
                path,
            )
        else:
            ingestion = IngestSource(
                None, None, chunks, None, embedding_provider(config, embedding)
            )
            chunk_count = ingestion.execute_indexing(job.source_version_id)
            element_count = 0
        execution = tracker.complete(
            job,
            execution,
            config,
            element_count,
            chunk_count,
            selected,
        )
        queue.complete(job, element_count, chunk_count)
    except Exception as error:
        logger.exception("Ingestion job %s failed", job.id)
        message = str(error)
        if execution is not None and execution.status is ExecutionStatus.RUNNING:
            try:
                execution = tracker.executions.fail(
                    execution,
                    error_code="ingestion_failed",
                    error_message=message[:4000],
                )
            except Exception:
                logger.exception(
                    "Failed to record execution failure for job %s", job.id
                )
        permanent = any(
            marker in message.lower()
            for marker in (
                "prepayment credits are depleted",
                "api key is invalid",
                "unsupported embedding provider",
            )
        )
        queue.fail(job, message, permanent=permanent)
    finally:
        if path is not None and temporary:
            cleanup_temp(path)
    return True
