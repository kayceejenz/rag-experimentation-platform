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
    folder_id: UUID | None


class KnowledgeFolderResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    parent_id: UUID | None
    name: str
    created_at: datetime


class KnowledgeFolderListResponse(BaseModel):
    folders: list[KnowledgeFolderResponse]


class CreateKnowledgeFolderRequest(BaseModel):
    name: str
    parent_id: UUID | None = None


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]


class SourceInspectionResponse(BaseModel):
    source_id: UUID
    version: int
    filename: str
    status: SourceStatus
    url: str


class KnowledgeActivityResponse(BaseModel):
    id: int
    event_type: str
    entity_id: UUID | None
    actor_user_id: UUID | None
    payload: dict
    occurred_at: datetime


class KnowledgeActivityListResponse(BaseModel):
    events: list[KnowledgeActivityResponse]
