from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class SpecificationKind(StrEnum):
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    PIPELINE = "pipeline"


@dataclass(frozen=True)
class Specification:
    project_id: UUID
    kind: SpecificationKind
    schema_version: int
    configuration: dict[str, Any]
    configuration_hash: str
    created_by: UUID | None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class SpecificationDependency:
    specification_id: UUID
    dependency_id: UUID
    role: str
    position: int = 0
