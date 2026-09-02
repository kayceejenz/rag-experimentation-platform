from datetime import datetime
from uuid import UUID

from modules.jobs.models.job_model import JobStatus
from modules.sources.models.source_model import SourceStatus
from pydantic import BaseModel


class IngestionJobResponse(BaseModel):
    id: UUID
    source_version_id: UUID
    source_id: UUID
    project_id: UUID
    knowledge_base_id: UUID
    filename: str
    status: JobStatus
    source_status: SourceStatus
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
