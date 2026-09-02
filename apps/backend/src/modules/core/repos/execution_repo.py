from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from modules.core.models.error_model import (
    ExecutionIdentityConflictError,
    InvalidExecutionTransitionError,
)
from modules.core.models.execution_model import (
    Execution,
    ExecutionArtifact,
    ExecutionKind,
    ExecutionStatus,
)
from psycopg.rows import dict_row


class ExecutionRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def create(self, execution: Execution) -> Execution:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "insert into ragapp.executions("
                "id,project_id,kind,specification_id,knowledge_base_id,status,idempotency_key,code_revision,"
                "attempt,parameters,created_by,created_at) "
                "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "on conflict do nothing returning *",
                (
                    execution.id,
                    execution.project_id,
                    execution.kind.value,
                    execution.specification_id,
                    execution.knowledge_base_id,
                    execution.status.value,
                    execution.idempotency_key,
                    execution.code_revision,
                    execution.attempt,
                    psycopg.types.json.Jsonb(execution.parameters),
                    execution.created_by,
                    execution.created_at,
                ),
            ).fetchone()
            if row is None and execution.idempotency_key is not None:
                row = db.execute(
                    "select * from ragapp.executions "
                    "where project_id=%s and kind=%s and idempotency_key=%s",
                    (
                        execution.project_id,
                        execution.kind.value,
                        execution.idempotency_key,
                    ),
                ).fetchone()
        if row is None:
            raise RuntimeError("Execution creation did not return a record")
        created = self._model(row)
        self._verify_identity(created, execution)
        return created

    def get(self, execution_id: UUID, project_id: UUID) -> Execution | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select * from ragapp.executions where id=%s and project_id=%s",
                (execution_id, project_id),
            ).fetchone()
        return self._model(row) if row else None

    def get_by_idempotency(
        self,
        project_id: UUID,
        kind: ExecutionKind,
        idempotency_key: str,
    ) -> Execution | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select * from ragapp.executions "
                "where project_id=%s and kind=%s and idempotency_key=%s",
                (project_id, kind.value, idempotency_key),
            ).fetchone()
        return self._model(row) if row else None

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
            "status='running',worker_id=%s,started_at=%s",
            (worker_id, started_at),
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
            "status='completed',result_summary=%s,completed_at=%s",
            (psycopg.types.json.Jsonb(result_summary), completed_at),
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
            "status='failed',error_code=%s,error_message=%s,completed_at=%s",
            (error_code, error_message, completed_at),
        )

    def cancel(
        self,
        execution_id: UUID,
        project_id: UUID,
        completed_at: datetime,
    ) -> Execution:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "update ragapp.executions set status='cancelled',completed_at=%s "
                "where id=%s and project_id=%s and status in ('pending','running') returning *",
                (completed_at, execution_id, project_id),
            ).fetchone()
        return self._transition_result(row, execution_id, project_id, "cancel")

    def add_input(self, link: ExecutionArtifact) -> ExecutionArtifact:
        return self._add_link("execution_inputs", link)

    def add_output(self, link: ExecutionArtifact) -> ExecutionArtifact:
        return self._add_link("execution_outputs", link)

    def complete_with_outputs(
        self,
        execution_id: UUID,
        project_id: UUID,
        outputs: list[ExecutionArtifact],
        result_summary: dict[str, Any],
        completed_at: datetime,
    ) -> Execution:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            for output in outputs:
                row = db.execute(
                    "insert into ragapp.execution_outputs("
                    "project_id,execution_id,artifact_id,role,position) "
                    "values(%s,%s,%s,%s,%s) on conflict do nothing returning *",
                    (
                        output.project_id,
                        output.execution_id,
                        output.artifact_id,
                        output.role,
                        output.position,
                    ),
                ).fetchone()
                if row is None:
                    row = db.execute(
                        "select * from ragapp.execution_outputs "
                        "where execution_id=%s and role=%s and position=%s",
                        (output.execution_id, output.role, output.position),
                    ).fetchone()
                if row is None or row["artifact_id"] != output.artifact_id:
                    raise ExecutionIdentityConflictError(
                        f"Lineage slot {output.role}[{output.position}] is already occupied"
                    )
            row = db.execute(
                "update ragapp.executions set status='completed',result_summary=%s,"
                "completed_at=%s where id=%s and project_id=%s and status='running' "
                "returning *",
                (
                    psycopg.types.json.Jsonb(result_summary),
                    completed_at,
                    execution_id,
                    project_id,
                ),
            ).fetchone()
            if row is None:
                raise InvalidExecutionTransitionError(
                    "Only a running execution can be finalized"
                )
        return self._model(row)

    def _transition(
        self,
        execution_id: UUID,
        project_id: UUID,
        expected: ExecutionStatus,
        assignment: str,
        values: tuple[Any, ...],
    ) -> Execution:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                f"update ragapp.executions set {assignment} "
                "where id=%s and project_id=%s and status=%s returning *",
                (*values, execution_id, project_id, expected.value),
            ).fetchone()
        return self._transition_result(row, execution_id, project_id, assignment)

    def _transition_result(
        self, row, execution_id: UUID, project_id: UUID, action: str
    ):
        if row is not None:
            return self._model(row)
        current = self.get(execution_id, project_id)
        state = current.status.value if current is not None else "missing"
        raise InvalidExecutionTransitionError(
            f"Cannot apply {action} to execution in {state} state"
        )

    def _add_link(self, table: str, link: ExecutionArtifact) -> ExecutionArtifact:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                f"insert into ragapp.{table}(project_id,execution_id,artifact_id,role,position) "
                "values(%s,%s,%s,%s,%s) on conflict do nothing returning *",
                (
                    link.project_id,
                    link.execution_id,
                    link.artifact_id,
                    link.role,
                    link.position,
                ),
            ).fetchone()
            if row is None:
                row = db.execute(
                    f"select * from ragapp.{table} "
                    "where execution_id=%s and role=%s and position=%s",
                    (link.execution_id, link.role, link.position),
                ).fetchone()
        if row is None or row["artifact_id"] != link.artifact_id:
            raise ExecutionIdentityConflictError(
                f"Lineage slot {link.role}[{link.position}] is already occupied"
            )
        return ExecutionArtifact(
            project_id=row["project_id"],
            execution_id=row["execution_id"],
            artifact_id=row["artifact_id"],
            role=row["role"],
            position=row["position"],
        )

    @staticmethod
    def _verify_identity(existing: Execution, requested: Execution) -> None:
        immutable_fields = (
            "project_id",
            "kind",
            "specification_id",
            "knowledge_base_id",
            "idempotency_key",
            "code_revision",
            "attempt",
            "parameters",
            "created_by",
        )
        if any(
            getattr(existing, field) != getattr(requested, field)
            for field in immutable_fields
        ):
            raise ExecutionIdentityConflictError(
                "Idempotency key resolved to different execution inputs"
            )

    @staticmethod
    def _model(row) -> Execution:
        return Execution(
            id=row["id"],
            project_id=row["project_id"],
            kind=ExecutionKind(row["kind"]),
            specification_id=row["specification_id"],
            knowledge_base_id=row.get("knowledge_base_id"),
            status=ExecutionStatus(row["status"]),
            idempotency_key=row["idempotency_key"],
            code_revision=row["code_revision"],
            worker_id=row["worker_id"],
            attempt=row["attempt"],
            parameters=dict(row["parameters"]),
            result_summary=(
                dict(row["result_summary"])
                if row["result_summary"] is not None
                else None
            ),
            error_code=row["error_code"],
            error_message=row["error_message"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )
