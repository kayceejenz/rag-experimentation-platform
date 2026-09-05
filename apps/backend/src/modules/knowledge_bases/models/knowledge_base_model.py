from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class KnowledgeBase:
    project_id: UUID
    created_by: UUID
    name: str = "Knowledge base"
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class KnowledgeBaseNotFoundError(Exception):
    pass


class KnowledgeBasePermissionError(Exception):
    pass
