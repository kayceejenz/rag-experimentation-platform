from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any
from uuid import UUID

from modules.core.contracts.execution_contract import ExecutionRepositoryContract
from modules.core.models.artifact_model import ArtifactKind, ArtifactStorageType
from modules.core.models.execution_model import (
    Execution,
    ExecutionKind,
    ExecutionStatus,
)
from modules.core.models.specification_model import SpecificationKind
from modules.core.services.artifact_service import ArtifactService
from modules.core.services.execution_service import ExecutionService
from modules.core.services.specification_service import SpecificationService
from modules.jobs.models.job_model import IngestionJob, PipelineStage

if TYPE_CHECKING:
    from core.settings import Settings


@dataclass(frozen=True)
class RecoveredIngestion:
    element_count: int
    chunk_count: int


class IngestionTracker:
    def __init__(
        self,
        artifacts: ArtifactService,
        specifications: SpecificationService,
        executions: ExecutionService,
        execution_repository: ExecutionRepositoryContract,
        code_revision: str,
    ) -> None:
        self.artifacts = artifacts
        self.specifications = specifications
        self.executions = executions
        self.execution_repository = execution_repository
        self.code_revision = code_revision

    def recover_previous_attempt(self, job: IngestionJob) -> RecoveredIngestion | None:
        if job.attempts <= 1:
            return None
        previous = None
        for attempt in range(job.attempts - 1, 0, -1):
            previous = self.execution_repository.get_by_idempotency(
                job.project_id,
                ExecutionKind.CHUNKING
                if job.stage is PipelineStage.CHUNK
                else ExecutionKind.INDEX_BUILD,
                execution_key(job.id, attempt),
            )
            if previous is not None:
                break
        if previous is None:
            return None
        if previous.status is ExecutionStatus.COMPLETED:
            summary = previous.result_summary or {}
            return RecoveredIngestion(
                element_count=int(summary["element_count"]),
                chunk_count=int(summary["chunk_count"]),
            )
        if previous.status is ExecutionStatus.RUNNING:
            self.executions.fail(
                previous,
                error_code="worker_lease_expired",
                error_message="Worker lease expired before execution completion",
            )
        elif previous.status is ExecutionStatus.PENDING:
            self.executions.cancel(previous)
        return None

    def begin(
        self,
        job: IngestionJob,
        config: Settings,
        worker_id: str,
        specification=None,
    ) -> Execution:
        specification = specification or self.specifications.register(
            job.project_id,
            job.uploaded_by,
            SpecificationKind.PIPELINE,
            1,
            ingestion_configuration(config),
        )
        if job.stage is PipelineStage.CHUNK:
            input_artifact = self.artifacts.register_content(
                job.project_id,
                job.uploaded_by,
                ArtifactKind.SOURCE,
                ArtifactStorageType.OBJECT,
                job.content_sha256,
                storage_key=job.storage_key,
                media_type=job.content_type,
                byte_size=job.byte_size,
            )
            input_role = "source_version"
        else:
            input_artifact = self.artifacts.register_manifest(
                job.project_id,
                job.uploaded_by,
                ArtifactKind.CHUNK_DATASET,
                {
                    "dataset": "ragapp.chunks",
                    "source_version_id": str(job.source_version_id),
                },
            )
            input_role = "chunks"
        execution = self.executions.create(
            job.project_id,
            job.uploaded_by,
            ExecutionKind.CHUNKING
            if job.stage is PipelineStage.CHUNK
            else ExecutionKind.INDEX_BUILD,
            self.code_revision,
            specification_id=specification.id,
            knowledge_base_id=job.knowledge_base_id,
            idempotency_key=execution_key(job.id, job.attempts),
            attempt=job.attempts,
            parameters={
                "stage": job.stage.value,
                "ingestion_job_id": str(job.id),
                "source_id": str(job.source_id),
                "source_version_id": str(job.source_version_id),
                "knowledge_base_id": str(job.knowledge_base_id),
            },
        )
        if execution.status is ExecutionStatus.PENDING:
            self.executions.add_input(execution, input_artifact, input_role)
            return self.executions.start(execution, worker_id)
        return execution

    def complete(
        self,
        job: IngestionJob,
        execution: Execution,
        config: Settings,
        element_count: int,
        chunk_count: int,
        configuration: dict[str, Any] | None = None,
    ) -> Execution:
        selected = configuration or ingestion_configuration(config)
        common_manifest = {
            "source_version_id": str(job.source_version_id),
            "specification_id": str(execution.specification_id),
        }
        elements = self.artifacts.register_manifest(
            job.project_id,
            job.uploaded_by,
            ArtifactKind.ELEMENT_DATASET,
            {
                **common_manifest,
                "dataset": "ragapp.source_elements",
                "row_count": element_count,
            },
        )
        chunks = self.artifacts.register_manifest(
            job.project_id,
            job.uploaded_by,
            ArtifactKind.CHUNK_DATASET,
            {
                **common_manifest,
                "dataset": "ragapp.chunks",
                "row_count": chunk_count,
            },
        )
        embeddings = self.artifacts.register_manifest(
            job.project_id,
            job.uploaded_by,
            ArtifactKind.EMBEDDING_DATASET,
            {
                **common_manifest,
                "dataset": "ragapp.chunk_embeddings",
                "row_count": chunk_count,
                "provider": selected["embedding"]["provider"],
                "model": selected["embedding"]["model"],
                "dimensions": selected["embedding"]["dimensions"],
            },
        )
        outputs = (
            [(elements, "elements", 0), (chunks, "chunks", 0)]
            if job.stage is PipelineStage.CHUNK
            else [(embeddings, "embeddings", 0)]
        )
        return self.executions.complete_with_outputs(
            execution,
            outputs,
            {"element_count": element_count, "chunk_count": chunk_count},
        )


def execution_key(job_id: UUID, attempt: int) -> str:
    return f"ingestion:{job_id}:attempt:{attempt}"


def ingestion_configuration(config: Settings) -> dict[str, Any]:
    return {
        "partitioning": {
            "provider": "unstructured",
            "strategy": config.unstructured_strategy,
            "pdf_strategy": config.unstructured_pdf_strategy,
            "ocr_languages": config.ocr_languages,
        },
        "chunking": {"strategy": "element"},
        "embedding": {
            "provider": config.embedding_provider,
            "model": config.embedding_model,
            "dimensions": config.embedding_dimensions,
        },
    }


def installed_code_revision() -> str:
    try:
        return f"ragapp-backend@{version('ragapp-backend')}"
    except PackageNotFoundError:
        return "ragapp-backend@development"
