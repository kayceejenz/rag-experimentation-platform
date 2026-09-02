from uuid import UUID

import psycopg
from modules.core.models.artifact_model import (
    Artifact,
    ArtifactKind,
    ArtifactStorageType,
)
from modules.core.models.execution_model import Execution
from modules.core.models.lineage_model import ArtifactLink, ExecutionLineage
from modules.core.models.specification_model import Specification, SpecificationKind
from modules.core.repos.execution_repo import ExecutionRepository
from psycopg.rows import dict_row


class LineageRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def list_executions(self, project_id: UUID, limit: int) -> list[Execution]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            rows = db.execute(
                "select * from ragapp.executions where project_id=%s "
                "order by created_at desc,id desc limit %s",
                (project_id, limit),
            ).fetchall()
        return [ExecutionRepository._model(row) for row in rows]

    def get_execution(
        self, project_id: UUID, execution_id: UUID
    ) -> ExecutionLineage | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            execution_row = db.execute(
                "select * from ragapp.executions where id=%s and project_id=%s",
                (execution_id, project_id),
            ).fetchone()
            if execution_row is None:
                return None
            specification_row = None
            if execution_row["specification_id"] is not None:
                specification_row = db.execute(
                    "select * from ragapp.specifications where id=%s and project_id=%s",
                    (execution_row["specification_id"], project_id),
                ).fetchone()
            inputs = self._links(db, "execution_inputs", project_id, execution_id)
            outputs = self._links(db, "execution_outputs", project_id, execution_id)
        return ExecutionLineage(
            execution=ExecutionRepository._model(execution_row),
            specification=self._specification(specification_row)
            if specification_row
            else None,
            inputs=tuple(inputs),
            outputs=tuple(outputs),
        )

    @staticmethod
    def _links(db, table: str, project_id: UUID, execution_id: UUID):
        rows = db.execute(
            f"select l.role,l.position,a.* from ragapp.{table} l "
            "join ragapp.artifacts a on a.id=l.artifact_id and a.project_id=l.project_id "
            "where l.project_id=%s and l.execution_id=%s order by l.role,l.position",
            (project_id, execution_id),
        ).fetchall()
        return [
            ArtifactLink(
                role=row["role"],
                position=row["position"],
                artifact=Artifact(
                    id=row["id"],
                    project_id=row["project_id"],
                    kind=ArtifactKind(row["kind"]),
                    storage_type=ArtifactStorageType(row["storage_type"]),
                    storage_key=row["storage_key"],
                    content_sha256=row["content_sha256"],
                    manifest=dict(row["manifest"])
                    if row["manifest"] is not None
                    else None,
                    manifest_hash=row["manifest_hash"],
                    media_type=row["media_type"],
                    byte_size=row["byte_size"],
                    created_by=row["created_by"],
                    created_at=row["created_at"],
                ),
            )
            for row in rows
        ]

    @staticmethod
    def _specification(row) -> Specification:
        return Specification(
            id=row["id"],
            project_id=row["project_id"],
            kind=SpecificationKind(row["kind"]),
            schema_version=row["schema_version"],
            configuration=dict(row["configuration"]),
            configuration_hash=row["configuration_hash"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )
