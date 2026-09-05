from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class KnowledgeBotStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class KnowledgeBot:
    project_id: UUID
    created_by: UUID
    name: str
    description: str | None = None
    status: KnowledgeBotStatus = KnowledgeBotStatus.ACTIVE
    settings: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    active_revision_version: int | None = None
    source_run_id: UUID | None = None
    source_variant_run_id: UUID | None = None
    source_experiment_name: str | None = None
    source_variant_name: str | None = None


class KnowledgeBotNotFoundError(Exception):
    pass


class KnowledgeBotPermissionError(Exception):
    pass
