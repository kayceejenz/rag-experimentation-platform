from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from modules.core.contracts.execution_contract import ExecutionRepositoryContract
from modules.core.models.artifact_model import Artifact
from modules.core.models.error_model import (
    InvalidExecutionTransitionError,
    InvalidLineageLinkError,
)
from modules.core.models.execution_model import (
    Execution,
    ExecutionArtifact,
    ExecutionKind,
    ExecutionStatus,
)


class ExecutionService:
    def __init__(
        self,
        repository: ExecutionRepositoryContract,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(UTC))

    def create(
        self,
        project_id: UUID,
        created_by: UUID | None,
        kind: ExecutionKind,
        code_revision: str,
        *,
        specification_id: UUID | None = None,
        idempotency_key: str | None = None,
        attempt: int = 1,
        parameters: dict[str, Any] | None = None,
    ) -> Execution:
        return self.repository.create(
            Execution(
                project_id=project_id,
                created_by=created_by,
                kind=kind,
                code_revision=code_revision,
                specification_id=specification_id,
                idempotency_key=idempotency_key,
                attempt=attempt,
                parameters=parameters or {},
            )
        )

    def start(self, execution: Execution, worker_id: str) -> Execution:
        self._require_status(execution, ExecutionStatus.PENDING)
        return self.repository.start(
            execution.id, execution.project_id, worker_id, self.clock()
        )

    def complete(
        self, execution: Execution, result_summary: dict[str, Any] | None = None
    ) -> Execution:
        self._require_status(execution, ExecutionStatus.RUNNING)
        return self.repository.complete(
            execution.id,
            execution.project_id,
            result_summary or {},
            self.clock(),
        )

    def fail(
        self,
        execution: Execution,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> Execution:
        self._require_status(execution, ExecutionStatus.RUNNING)
        if error_code is None and error_message is None:
            raise ValueError("A failed execution requires an error code or message")
        return self.repository.fail(
            execution.id,
            execution.project_id,
            error_code,
            error_message,
            self.clock(),
        )

    def cancel(self, execution: Execution) -> Execution:
        if execution.status not in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            raise InvalidExecutionTransitionError(
                f"Cannot cancel execution in {execution.status.value} state"
            )
        return self.repository.cancel(execution.id, execution.project_id, self.clock())

    def add_input(
        self,
        execution: Execution,
        artifact: Artifact,
        role: str,
        position: int = 0,
    ) -> ExecutionArtifact:
        self._require_same_project(execution, artifact)
        self._require_status(execution, ExecutionStatus.PENDING)
        return self.repository.add_input(
            ExecutionArtifact(
                project_id=execution.project_id,
                execution_id=execution.id,
                artifact_id=artifact.id,
                role=role,
                position=position,
            )
        )

    def add_output(
        self,
        execution: Execution,
        artifact: Artifact,
        role: str,
        position: int = 0,
    ) -> ExecutionArtifact:
        self._require_same_project(execution, artifact)
        self._require_status(execution, ExecutionStatus.RUNNING)
        return self.repository.add_output(
            ExecutionArtifact(
                project_id=execution.project_id,
                execution_id=execution.id,
                artifact_id=artifact.id,
                role=role,
                position=position,
            )
        )

    @staticmethod
    def _require_status(execution: Execution, expected: ExecutionStatus) -> None:
        if execution.status is not expected:
            raise InvalidExecutionTransitionError(
                f"Expected {expected.value} execution, got {execution.status.value}"
            )

    @staticmethod
    def _require_same_project(execution: Execution, artifact: Artifact) -> None:
        if execution.project_id != artifact.project_id:
            raise InvalidLineageLinkError(
                "Execution and artifact must belong to the same project"
            )
