from collections.abc import Mapping
from typing import Any
from uuid import UUID

from modules.core.contracts.artifact_contract import ArtifactRepositoryContract
from modules.core.helpers.canonical_json import canonical_json
from modules.core.models.artifact_model import Artifact, ArtifactKind, ArtifactStorageType


class ArtifactService:
    def __init__(self, repository: ArtifactRepositoryContract) -> None:
        self.repository = repository

    def register_content(
        self,
        project_id: UUID,
        created_by: UUID | None,
        kind: ArtifactKind,
        storage_type: ArtifactStorageType,
        content_sha256: str,
        *,
        storage_key: str | None = None,
        media_type: str | None = None,
        byte_size: int | None = None,
    ) -> Artifact:
        return self.repository.register(
            Artifact(
                project_id=project_id,
                created_by=created_by,
                kind=kind,
                storage_type=storage_type,
                storage_key=storage_key,
                content_sha256=content_sha256,
                media_type=media_type,
                byte_size=byte_size,
            )
        )

    def register_manifest(
        self,
        project_id: UUID,
        created_by: UUID | None,
        kind: ArtifactKind,
        manifest: Mapping[str, Any],
        *,
        storage_type: ArtifactStorageType = ArtifactStorageType.DATABASE,
        storage_key: str | None = None,
        media_type: str | None = None,
        byte_size: int | None = None,
    ) -> Artifact:
        identity = canonical_json(dict(manifest))
        return self.repository.register(
            Artifact(
                project_id=project_id,
                created_by=created_by,
                kind=kind,
                storage_type=storage_type,
                storage_key=storage_key,
                manifest=identity.value,
                manifest_hash=identity.sha256,
                media_type=media_type,
                byte_size=byte_size,
            )
        )
