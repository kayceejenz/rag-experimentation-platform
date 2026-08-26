import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from modules.core.models.artifact_model import Artifact, ArtifactKind, ArtifactStorageType
from modules.core.models.error_model import (
    ExecutionIdentityConflictError,
    InvalidExecutionTransitionError,
    InvalidLineageLinkError,
)
from modules.core.models.execution_model import (
    Execution,
    ExecutionArtifact,
    ExecutionKind,
    ExecutionStatus,
)
from modules.core.services.execution_service import ExecutionService


class InMemoryExecutionRepository:
    def __init__(self) -> None:
        self.executions: dict[UUID, Execution] = {}
        self.idempotency: dict[tuple[UUID, ExecutionKind, str], UUID] = {}
        self.inputs: dict[tuple[UUID, str, int], ExecutionArtifact] = {}
        self.outputs: dict[tuple[UUID, str, int], ExecutionArtifact] = {}

    def create(self, execution: Execution) -> Execution:
        if execution.idempotency_key is not None:
            key = (execution.project_id, execution.kind, execution.idempotency_key)
            existing_id = self.idempotency.get(key)
            if existing_id is not None:
                existing = self.executions[existing_id]
                comparable = (
                    "project_id",
                    "kind",
                    "specification_id",
                    "idempotency_key",
                    "code_revision",
                    "attempt",
                    "parameters",
                    "created_by",
                )
                if any(
                    getattr(existing, field) != getattr(execution, field)
                    for field in comparable
                ):
                    raise ExecutionIdentityConflictError("Conflicting execution inputs")
                return existing
            self.idempotency[key] = execution.id
        self.executions[execution.id] = execution
        return execution

    def get(self, execution_id: UUID, project_id: UUID) -> Execution | None:
        execution = self.executions.get(execution_id)
        return execution if execution and execution.project_id == project_id else None

    def get_by_idempotency(
        self,
        project_id: UUID,
        kind: ExecutionKind,
        idempotency_key: str,
    ) -> Execution | None:
        return next(
            (
                execution
                for execution in self.executions.values()
                if execution.project_id == project_id
                and execution.kind is kind
                and execution.idempotency_key == idempotency_key
            ),
            None,
        )

    def start(
        self,
        execution_id: UUID,
        project_id: UUID,
        worker_id: str,
        started_at: datetime,
    ) -> Execution:
        return self._transition(
            execution_id,
            project_id,
            ExecutionStatus.PENDING,
            status=ExecutionStatus.RUNNING,
            worker_id=worker_id,
            started_at=started_at,
        )

    def complete(
        self,
        execution_id: UUID,
        project_id: UUID,
        result_summary: dict[str, Any],
        completed_at: datetime,
    ) -> Execution:
        return self._transition(
            execution_id,
            project_id,
            ExecutionStatus.RUNNING,
            status=ExecutionStatus.COMPLETED,
            result_summary=result_summary,
            completed_at=completed_at,
        )

    def fail(
        self,
        execution_id: UUID,
        project_id: UUID,
        error_code: str | None,
        error_message: str | None,
        completed_at: datetime,
    ) -> Execution:
        return self._transition(
            execution_id,
            project_id,
            ExecutionStatus.RUNNING,
            status=ExecutionStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
            completed_at=completed_at,
        )

    def cancel(
        self,
        execution_id: UUID,
        project_id: UUID,
        completed_at: datetime,
    ) -> Execution:
        current = self.executions[execution_id]
        if current.project_id != project_id or current.status not in (
            ExecutionStatus.PENDING,
            ExecutionStatus.RUNNING,
        ):
            raise InvalidExecutionTransitionError("Cannot cancel")
        updated = replace(
            current, status=ExecutionStatus.CANCELLED, completed_at=completed_at
        )
        self.executions[execution_id] = updated
        return updated

    def add_input(self, link: ExecutionArtifact) -> ExecutionArtifact:
        return self._add_link(self.inputs, link)

    def add_output(self, link: ExecutionArtifact) -> ExecutionArtifact:
        return self._add_link(self.outputs, link)

    def complete_with_outputs(
        self,
        execution_id: UUID,
        project_id: UUID,
        outputs: list[ExecutionArtifact],
        result_summary: dict[str, Any],
        completed_at: datetime,
    ) -> Execution:
        current = self.executions[execution_id]
        if current.project_id != project_id or current.status is not ExecutionStatus.RUNNING:
            raise InvalidExecutionTransitionError("Only running executions can be finalized")
        for output in outputs:
            key = (output.execution_id, output.role, output.position)
            existing = self.outputs.get(key)
            if existing is not None and existing.artifact_id != output.artifact_id:
                raise ExecutionIdentityConflictError("Lineage slot is occupied")
        for output in outputs:
            self._add_link(self.outputs, output)
        completed = replace(
            current,
            status=ExecutionStatus.COMPLETED,
            result_summary=result_summary,
            completed_at=completed_at,
        )
        self.executions[execution_id] = completed
        return completed

    def _transition(
        self,
        execution_id: UUID,
        project_id: UUID,
        expected: ExecutionStatus,
        **changes,
    ) -> Execution:
        current = self.executions[execution_id]
        if current.project_id != project_id or current.status is not expected:
            raise InvalidExecutionTransitionError("Invalid transition")
        updated = replace(current, **changes)
        self.executions[execution_id] = updated
        return updated

    @staticmethod
    def _add_link(
        links: dict[tuple[UUID, str, int], ExecutionArtifact],
        link: ExecutionArtifact,
    ) -> ExecutionArtifact:
        key = (link.execution_id, link.role, link.position)
        existing = links.setdefault(key, link)
        if existing.artifact_id != link.artifact_id:
            raise ExecutionIdentityConflictError("Lineage slot is occupied")
        return existing


class ExecutionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryExecutionRepository()
        self.created_at = datetime(2026, 8, 26, 12, tzinfo=UTC)
        self.now = self.created_at + timedelta(seconds=1)
        self.service = ExecutionService(self.repository, clock=lambda: self.now)
        self.project_id = uuid4()
        self.user_id = uuid4()

    def create_execution(self, **overrides) -> Execution:
        values = {
            "project_id": self.project_id,
            "created_by": self.user_id,
            "kind": ExecutionKind.INGESTION,
            "code_revision": "ec795de",
            "idempotency_key": "ingestion-job:one:attempt:1",
            "parameters": {"source_version_id": str(uuid4())},
        }
        values.update(overrides)
        return self.service.create(**values)

    def artifact(self, project_id: UUID | None = None) -> Artifact:
        return Artifact(
            project_id=project_id or self.project_id,
            kind=ArtifactKind.SOURCE,
            storage_type=ArtifactStorageType.OBJECT,
            storage_key=f"sources/{uuid4()}",
            content_sha256="a" * 64,
            created_by=self.user_id,
        )

    def test_execution_follows_pending_running_completed_lifecycle(self) -> None:
        pending = self.create_execution()
        running = self.service.start(pending, "worker-1")
        self.now += timedelta(seconds=1)
        completed = self.service.complete(running, {"chunk_count": 12})

        self.assertEqual(ExecutionStatus.COMPLETED, completed.status)
        self.assertEqual("worker-1", completed.worker_id)
        self.assertEqual({"chunk_count": 12}, completed.result_summary)
        self.assertIsNotNone(completed.started_at)
        self.assertIsNotNone(completed.completed_at)

    def test_idempotency_returns_same_execution(self) -> None:
        parameters = {"source_version_id": str(uuid4())}
        first = self.create_execution(parameters=parameters)
        second = self.create_execution(parameters=parameters)

        self.assertEqual(first.id, second.id)
        self.assertEqual(1, len(self.repository.executions))

    def test_idempotency_rejects_different_inputs(self) -> None:
        self.create_execution(parameters={"source_version_id": "first"})
        with self.assertRaises(ExecutionIdentityConflictError):
            self.create_execution(parameters={"source_version_id": "second"})

    def test_input_must_be_added_before_start_and_output_after_start(self) -> None:
        pending = self.create_execution()
        source = self.artifact()
        input_link = self.service.add_input(pending, source, "source_version")
        running = self.service.start(pending, "worker-1")

        with self.assertRaises(InvalidExecutionTransitionError):
            self.service.add_input(running, source, "late_source")
        output_link = self.service.add_output(running, source, "chunks")

        self.assertEqual(source.id, input_link.artifact_id)
        self.assertEqual(source.id, output_link.artifact_id)

    def test_cross_project_lineage_is_rejected(self) -> None:
        pending = self.create_execution()
        with self.assertRaises(InvalidLineageLinkError):
            self.service.add_input(pending, self.artifact(uuid4()), "source_version")

    def test_outputs_and_completion_are_finalized_together(self) -> None:
        running = self.service.start(self.create_execution(), "worker-1")
        elements = self.artifact()
        chunks = self.artifact()

        completed = self.service.complete_with_outputs(
            running,
            [(elements, "elements", 0), (chunks, "chunks", 0)],
            {"element_count": 2, "chunk_count": 2},
        )

        self.assertEqual(ExecutionStatus.COMPLETED, completed.status)
        self.assertEqual(2, len(self.repository.outputs))

    def test_output_collision_leaves_execution_running(self) -> None:
        running = self.service.start(self.create_execution(), "worker-1")
        occupied = self.artifact()
        requested = self.artifact()
        self.service.add_output(running, occupied, "chunks")

        with self.assertRaises(ExecutionIdentityConflictError):
            self.service.complete_with_outputs(
                running,
                [(requested, "chunks", 0)],
                {"chunk_count": 1},
            )

        self.assertEqual(
            ExecutionStatus.RUNNING,
            self.repository.executions[running.id].status,
        )

    def test_terminal_execution_cannot_transition_again(self) -> None:
        running = self.service.start(self.create_execution(), "worker-1")
        failed = self.service.fail(running, error_message="provider unavailable")

        with self.assertRaises(InvalidExecutionTransitionError):
            self.service.start(failed, "worker-2")
        with self.assertRaises(InvalidExecutionTransitionError):
            self.service.cancel(failed)

    def test_failure_requires_diagnostic_information(self) -> None:
        running = self.service.start(self.create_execution(), "worker-1")
        with self.assertRaisesRegex(ValueError, "error code or message"):
            self.service.fail(running)


if __name__ == "__main__":
    unittest.main()
