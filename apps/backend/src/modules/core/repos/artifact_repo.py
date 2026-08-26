from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from modules.core.models.artifact_model import Artifact, ArtifactKind, ArtifactStorageType
from modules.core.models.error_model import ArtifactIdentityConflictError


class ArtifactRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def register(self, artifact: Artifact) -> Artifact:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "insert into ragapp.artifacts("
                "id,project_id,kind,storage_type,storage_key,content_sha256,manifest,"
                "manifest_hash,media_type,byte_size,created_by) "
                "values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "on conflict do nothing returning *",
                (
                    artifact.id,
                    artifact.project_id,
                    artifact.kind.value,
                    artifact.storage_type.value,
                    artifact.storage_key,
                    artifact.content_sha256,
                    psycopg.types.json.Jsonb(artifact.manifest)
                    if artifact.manifest is not None
                    else None,
                    artifact.manifest_hash,
                    artifact.media_type,
                    artifact.byte_size,
                    artifact.created_by,
                ),
            ).fetchone()
            if row is None:
                row = self._find_existing(db, artifact)
        if row is None:
            raise RuntimeError("Artifact registration did not return a record")
        registered = self._model(row)
        self._verify_identity(registered, artifact)
        return registered

    def get(self, artifact_id: UUID, project_id: UUID) -> Artifact | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as db:
            row = db.execute(
                "select * from ragapp.artifacts where id=%s and project_id=%s",
                (artifact_id, project_id),
            ).fetchone()
        return self._model(row) if row else None

    @staticmethod
    def _find_existing(db, artifact: Artifact):
        if artifact.content_sha256 is not None:
            row = db.execute(
                "select * from ragapp.artifacts "
                "where project_id=%s and kind=%s and content_sha256=%s",
                (artifact.project_id, artifact.kind.value, artifact.content_sha256),
            ).fetchone()
            if row is not None:
                return row
        if artifact.manifest_hash is not None:
            row = db.execute(
                "select * from ragapp.artifacts "
                "where project_id=%s and kind=%s and manifest_hash=%s",
                (artifact.project_id, artifact.kind.value, artifact.manifest_hash),
            ).fetchone()
            if row is not None:
                return row
        if artifact.storage_key is not None:
            return db.execute(
                "select * from ragapp.artifacts "
                "where project_id=%s and storage_type=%s and storage_key=%s",
                (
                    artifact.project_id,
                    artifact.storage_type.value,
                    artifact.storage_key,
                ),
            ).fetchone()
        return None

    @staticmethod
    def _verify_identity(existing: Artifact, requested: Artifact) -> None:
        content_conflict = (
            requested.content_sha256 is not None
            and existing.content_sha256 != requested.content_sha256
        )
        manifest_conflict = (
            requested.manifest_hash is not None
            and (
                existing.manifest_hash != requested.manifest_hash
                or existing.manifest != requested.manifest
            )
        )
        if existing.kind is not requested.kind or content_conflict or manifest_conflict:
            raise ArtifactIdentityConflictError(
                "Artifact identity resolved to different immutable content"
            )

    @staticmethod
    def _model(row) -> Artifact:
        return Artifact(
            id=row["id"],
            project_id=row["project_id"],
            kind=ArtifactKind(row["kind"]),
            storage_type=ArtifactStorageType(row["storage_type"]),
            storage_key=row["storage_key"],
            content_sha256=row["content_sha256"],
            manifest=dict(row["manifest"]) if row["manifest"] is not None else None,
            manifest_hash=row["manifest_hash"],
            media_type=row["media_type"],
            byte_size=row["byte_size"],
            created_by=row["created_by"],
            created_at=row["created_at"],
        )
