from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class SourceStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class Source:
    project_id: UUID
    knowledge_base_id: UUID
    uploaded_by: UUID
    display_name: str
    version_id: UUID
    version: int
    filename: str
    content_type: str
    storage_key: str
    byte_size: int
    id: UUID = field(default_factory=uuid4)
    job_id: UUID | None = None
    status: SourceStatus = SourceStatus.UPLOADED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
