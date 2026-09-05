from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(StrEnum):
    CHUNK = "chunk"
    INDEX = "index"


@dataclass(frozen=True)
class IngestionJob:
    source_version_id: UUID
    source_id: UUID
    project_id: UUID
    knowledge_base_id: UUID
    storage_key: str
    uploaded_by: UUID
    content_type: str
    byte_size: int
    content_sha256: str
    stage: PipelineStage = PipelineStage.CHUNK
    specification_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    max_attempts: int = 5
    available_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class IngestionJobDetails:
    id: UUID
    source_version_id: UUID
    source_id: UUID
    project_id: UUID
    knowledge_base_id: UUID
    filename: str
    status: JobStatus
    source_status: str
    attempts: int
    max_attempts: int
    element_count: int
    chunk_count: int
    last_error: str | None
    available_at: datetime
    created_at: datetime
    updated_at: datetime
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    completed_at: datetime | None
