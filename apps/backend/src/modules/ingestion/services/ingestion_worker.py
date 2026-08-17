import logging
import socket

from core.settings import Settings
from integrations.embeddings import GeminiEmbedder
from integrations.ingestion_store import ChunkRepository, ElementAssetStore, ElementRepository
from integrations.partitioner import UnstructuredPartitioner
from integrations.storage import cleanup_temp, resolve_file
from modules.ingestion.services.ingestion_service import IngestSource
from modules.jobs.repos.job_repo import JobRepository

logger = logging.getLogger(__name__)


def embedding_provider(config: Settings):
    provider = config.embedding_provider.lower()
    if provider == "gemini":
        if not config.effective_embedding_api_key:
            raise RuntimeError("EMBEDDING_API_KEY or LLM_API_KEY is required for Gemini embeddings")
        return GeminiEmbedder(
            api_key=config.effective_embedding_api_key,
            model=config.embedding_model,
            dimensions=config.embedding_dimensions,
            base_url=config.gemini_api_url,
            batch_size=config.embedding_batch_size,
        )
    raise RuntimeError(f"Unsupported embedding provider: {config.embedding_provider}")


def run_once(config: Settings) -> bool:
    if not config.database_url:
        return False
    queue = JobRepository(config.database_url)
    job = queue.claim_next(socket.gethostname())
    if not job:
        return False

    path = None
    temporary = False
    try:
        if not config.unstructured_api_key:
            raise RuntimeError("UNSTRUCTURED_API_KEY is required for ingestion")
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
            ),
            ElementRepository(config.database_url),
            ChunkRepository(
                config.database_url, config.embedding_provider.lower(), config.embedding_model
            ),
            ElementAssetStore(config.source_storage_dir),
            embedding_provider(config),
        )
        element_count, chunk_count = ingestion.execute(
            job.project_id,
            job.source_id,
            job.source_version_id,
            job.knowledge_base_id,
            path,
        )
        queue.complete(job, element_count, chunk_count)
    except Exception as error:
        logger.exception("Ingestion job %s failed", job.id)
        message = str(error)
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
