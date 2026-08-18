from datetime import datetime
from typing import Any
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


class SourceElementResponse(BaseModel):
    element_id: str
    parent_element_id: str | None
    category: str
    content: str
    page_number: int | None
    coordinates: Any | None
    table_html: str | None
    metadata: dict[str, Any]
    sequence_number: int


class SourceChunkResponse(BaseModel):
    id: UUID
    position: int
    content: str
    token_count: int | None
    page_from: int | None
    page_to: int | None
    metadata: dict[str, Any]
    element_ids: list[str]


class SourceInspectionResponse(BaseModel):
    source_id: UUID
    version_id: UUID
    version: int
    filename: str
    status: SourceStatus
    parser_name: str | None
    parser_version: str | None
    parser_config: dict[str, Any]
    element_count: int
    chunk_count: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    elements: list[SourceElementResponse]
    chunks: list[SourceChunkResponse]
