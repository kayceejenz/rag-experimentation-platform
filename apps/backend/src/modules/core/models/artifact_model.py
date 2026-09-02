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
        for name, value in (
            ("content_sha256", self.content_sha256),
            ("manifest_hash", self.manifest_hash),
        ):
            if value is not None and (
                len(value) != 64
                or any(char not in "0123456789abcdef" for char in value)
            ):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        if self.storage_key is not None and not self.storage_key.strip():
            raise ValueError("storage_key cannot be blank")
        if self.storage_type is ArtifactStorageType.OBJECT and self.storage_key is None:
            raise ValueError("Object artifacts require a storage_key")
        if self.byte_size is not None and self.byte_size < 0:
            raise ValueError("byte_size cannot be negative")
        if self.manifest is None and self.manifest_hash is not None:
            raise ValueError("manifest_hash requires a manifest")
