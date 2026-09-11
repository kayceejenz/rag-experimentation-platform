import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from modules.core.models.artifact_model import (
    Artifact,
    ArtifactKind,
    ArtifactStorageType,
)
from modules.core.models.execution_model import (
    Execution,
    ExecutionKind,
    ExecutionStatus,
)
from modules.core.models.specification_model import Specification, SpecificationKind
from modules.ingestion.services.ingestion_specification import (
    normalize_ingestion_pipeline,
)
from modules.ingestion.services.ingestion_tracking_service import (
    IngestionTracker,
    execution_key,
)
from modules.jobs.models.job_model import IngestionJob


class IngestionTrackingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = MagicMock()
        self.specifications = MagicMock()
        self.executions = MagicMock()
        self.execution_repository = MagicMock()
        self.tracker = IngestionTracker(
            self.artifacts,
            self.specifications,
            self.executions,
            self.execution_repository,
            "ragapp-backend@0.1.0",
        )
        self.job = IngestionJob(
            id=uuid4(),
            project_id=uuid4(),
            source_id=uuid4(),
            source_version_id=uuid4(),
            knowledge_base_id=uuid4(),
            uploaded_by=uuid4(),
            storage_key="sources/document.pdf",
            content_type="application/pdf",
            byte_size=1234,
            content_sha256="a" * 64,
            attempts=1,
        )
        self.config = SimpleNamespace(
            embedding_provider="gemini",
            embedding_model="embedding-model",
            embedding_dimensions=768,
            unstructured_strategy="auto",
            unstructured_pdf_strategy="hi_res",
            ocr_languages=["fra", "eng"],
        )

    def test_pipeline_normalization_is_deterministic(self) -> None:
        normalized = normalize_ingestion_pipeline(
            {
                "embedding": {
                    "model": "embedding-model",
                    "dimensions": "768",
                    "provider": "GEMINI",
                },
                "partitioning": {"ocr_languages": ["fra", "eng", "eng"]},
                "chunking": {},
            }
        )

        self.assertEqual(["eng", "fra"], normalized["partitioning"]["ocr_languages"])
        self.assertEqual("auto", normalized["partitioning"]["strategy"])
        self.assertEqual("element", normalized["chunking"]["strategy"])
        self.assertEqual("gemini", normalized["embedding"]["provider"])

    def test_begin_registers_specification_source_and_running_execution(self) -> None:
        specification = Specification(
            project_id=self.job.project_id,
            kind=SpecificationKind.PIPELINE,
            schema_version=1,
            configuration={},
            configuration_hash="b" * 64,
            created_by=self.job.uploaded_by,
        )
        source = Artifact(
            project_id=self.job.project_id,
            kind=ArtifactKind.SOURCE,
            storage_type=ArtifactStorageType.OBJECT,
            storage_key=self.job.storage_key,
            content_sha256=self.job.content_sha256,
            created_by=self.job.uploaded_by,
        )
        pending = Execution(
            project_id=self.job.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
            specification_id=specification.id,
            idempotency_key=execution_key(self.job.id, 1),
            created_by=self.job.uploaded_by,
        )
        running = replace(pending, status=ExecutionStatus.RUNNING, worker_id="worker-1")
        self.specifications.register.return_value = specification
        self.artifacts.register_content.return_value = source
        self.executions.create.return_value = pending
        self.executions.start.return_value = running

        result = self.tracker.begin(self.job, self.config, "worker-1")

        self.assertEqual(ExecutionStatus.RUNNING, result.status)
        self.executions.add_input.assert_called_once_with(
            pending, source, "source_version"
        )
        self.executions.create.assert_called_once()
        create_arguments = self.executions.create.call_args
        self.assertEqual("ragapp-backend@0.1.0", create_arguments.args[3])
        self.assertEqual(
            execution_key(self.job.id, 1),
            create_arguments.kwargs["idempotency_key"],
        )

    def test_completed_previous_attempt_is_recovered_without_new_execution(
        self,
    ) -> None:
        retried_job = replace(self.job, attempts=2)
        completed = Execution(
            project_id=self.job.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
            status=ExecutionStatus.COMPLETED,
            result_summary={"element_count": 8, "chunk_count": 6},
        )
        self.execution_repository.get_by_idempotency.return_value = completed

        recovered = self.tracker.recover_previous_attempt(retried_job)

        self.assertIsNotNone(recovered)
        self.assertEqual(8, recovered.element_count)
        self.assertEqual(6, recovered.chunk_count)
        self.executions.fail.assert_not_called()

    def test_recovery_skips_attempts_that_died_before_execution_creation(self) -> None:
        retried_job = replace(self.job, attempts=3)
        completed = Execution(
            project_id=self.job.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
            status=ExecutionStatus.COMPLETED,
            result_summary={"element_count": 5, "chunk_count": 4},
        )
        self.execution_repository.get_by_idempotency.side_effect = [None, completed]

        recovered = self.tracker.recover_previous_attempt(retried_job)

        self.assertIsNotNone(recovered)
        self.assertEqual(5, recovered.element_count)
        self.assertEqual(2, self.execution_repository.get_by_idempotency.call_count)

    def test_expired_running_attempt_is_failed_before_retry(self) -> None:
        retried_job = replace(self.job, attempts=2)
        running = Execution(
            project_id=self.job.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
            status=ExecutionStatus.RUNNING,
        )
        self.execution_repository.get_by_idempotency.return_value = running

        recovered = self.tracker.recover_previous_attempt(retried_job)

        self.assertIsNone(recovered)
        self.executions.fail.assert_called_once_with(
            running,
            error_code="worker_lease_expired",
            error_message="Worker lease expired before execution completion",
        )

    def test_chunk_completion_links_prepared_dataset_outputs(self) -> None:
        running = Execution(
            project_id=self.job.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
            specification_id=uuid4(),
            status=ExecutionStatus.RUNNING,
        )
        outputs = [
            Artifact(
                project_id=self.job.project_id,
                kind=kind,
                storage_type=ArtifactStorageType.DATABASE,
                manifest={"dataset": kind.value},
                manifest_hash=character * 64,
                created_by=self.job.uploaded_by,
            )
            for kind, character in (
                (ArtifactKind.ELEMENT_DATASET, "c"),
                (ArtifactKind.CHUNK_DATASET, "d"),
                (ArtifactKind.EMBEDDING_DATASET, "e"),
            )
        ]
        completed = replace(
            running,
            status=ExecutionStatus.COMPLETED,
            result_summary={"element_count": 8, "chunk_count": 6},
        )
        self.artifacts.register_manifest.side_effect = outputs
        self.executions.complete_with_outputs.return_value = completed

        result = self.tracker.complete(self.job, running, self.config, 8, 6)

        self.assertEqual(ExecutionStatus.COMPLETED, result.status)
        self.assertEqual(3, self.artifacts.register_manifest.call_count)
        self.executions.complete_with_outputs.assert_called_once_with(
            running,
            [
                (outputs[0], "elements", 0),
                (outputs[1], "chunks", 0),
            ],
            {"element_count": 8, "chunk_count": 6},
        )


if __name__ == "__main__":
    unittest.main()
