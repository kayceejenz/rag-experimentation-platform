from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from modules.core.models.execution_model import (
    Execution,
    ExecutionArtifact,
    ExecutionKind,
)


class ExecutionRepositoryContract(Protocol):
    def create(self, execution: Execution) -> Execution: ...

    def get(self, execution_id: UUID, project_id: UUID) -> Execution | None: ...

    def get_by_idempotency(
        self,
        project_id: UUID,
        kind: ExecutionKind,
        idempotency_key: str,
    ) -> Execution | None: ...

    def start(
        self,
        execution_id: UUID,
        project_id: UUID,
        worker_id: str,
        started_at: datetime,
    ) -> Execution: ...

    def complete(
        self,
        execution_id: UUID,
        project_id: UUID,
        result_summary: dict[str, Any],
        completed_at: datetime,
    ) -> Execution: ...

    def fail(
        self,
        execution_id: UUID,
        project_id: UUID,
        error_code: str | None,
        error_message: str | None,
        completed_at: datetime,
    ) -> Execution: ...

    def cancel(
        self,
        execution_id: UUID,
        project_id: UUID,
        completed_at: datetime,
    ) -> Execution: ...

    def add_input(self, link: ExecutionArtifact) -> ExecutionArtifact: ...

    def add_output(self, link: ExecutionArtifact) -> ExecutionArtifact: ...

    def complete_with_outputs(
        self,
        execution_id: UUID,
        project_id: UUID,
        outputs: list[ExecutionArtifact],
        result_summary: dict[str, Any],
        completed_at: datetime,
    ) -> Execution: ...
