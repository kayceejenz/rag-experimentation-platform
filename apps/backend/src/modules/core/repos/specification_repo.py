from uuid import UUID

import psycopg
from modules.core.models.error_model import SpecificationHashCollisionError
from modules.core.models.specification_model import Specification, SpecificationKind
from psycopg.rows import dict_row


class SpecificationRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def register(self, specification: Specification) -> Specification:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "insert into ragapp.specifications("
                "id,project_id,kind,schema_version,configuration,configuration_hash,created_by) "
                "values(%s,%s,%s,%s,%s,%s,%s) "
                "on conflict(project_id,kind,schema_version,configuration_hash) do nothing "
                "returning *",
                (
                    specification.id,
                    specification.project_id,
                    specification.kind.value,
                    specification.schema_version,
                    psycopg.types.json.Jsonb(specification.configuration),
                    specification.configuration_hash,
                    specification.created_by,
                ),
            ).fetchone()
            if row is None:
                row = db.execute(
                    "select * from ragapp.specifications "
                    "where project_id=%s and kind=%s and schema_version=%s "
                    "and configuration_hash=%s",
                    (
                        specification.project_id,
                        specification.kind.value,
                        specification.schema_version,
                        specification.configuration_hash,
                    ),
                ).fetchone()
        if row is None:
            raise RuntimeError("Specification registration did not return a record")
        registered = self._model(row)
        if registered.configuration != specification.configuration:
            raise SpecificationHashCollisionError(
                "Specification hash resolved to different configuration content"
            )
        return registered

    def get(self, specification_id: UUID, project_id: UUID) -> Specification | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select * from ragapp.specifications where id=%s and project_id=%s",
                (specification_id, project_id),
            ).fetchone()
        return self._model(row) if row else None

    @staticmethod
    def _model(row) -> Specification:
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
