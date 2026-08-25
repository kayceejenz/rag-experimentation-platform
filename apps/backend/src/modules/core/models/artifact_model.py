from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ArtifactKind(StrEnum):
    SOURCE = "source"
    ELEMENT_DATASET = "element_dataset"
    CHUNK_DATASET = "chunk_dataset"
    EMBEDDING_DATASET = "embedding_dataset"
    REPORT = "report"


class ArtifactStorageType(StrEnum):
    OBJECT = "object"
    DATABASE = "database"
    EXTERNAL = "external"


@dataclass(frozen=True)
class Artifact:
    project_id: UUID
    kind: ArtifactKind
    storage_type: ArtifactStorageType
    created_by: UUID | None
    storage_key: str | None = None
    content_sha256: str | None = None
    manifest: dict[str, Any] | None = None
    manifest_hash: str | None = None
    media_type: str | None = None
    byte_size: int | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.content_sha256 is None and self.manifest_hash is None:
            raise ValueError("Artifact requires a content or manifest hash")
