from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from modules.sources.models.source_model import SourceStatus


class SourceResponse(BaseModel):
    id: UUID
    project_id: UUID
    knowledge_base_id: UUID
    uploaded_by: UUID
    display_name: str
    version_id: UUID
    job_id: UUID | None
    version: int
    filename: str
    content_type: str
    byte_size: int
    status: SourceStatus
    created_at: datetime


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
