from datetime import datetime
from typing import Any
from uuid import UUID

from modules.core.models.artifact_model import ArtifactKind, ArtifactStorageType
from modules.core.models.execution_model import ExecutionKind, ExecutionStatus
from modules.core.models.specification_model import SpecificationKind
from pydantic import BaseModel


class ExecutionResponse(BaseModel):
    id: UUID
    project_id: UUID
    kind: ExecutionKind
    specification_id: UUID | None
    knowledge_base_id: UUID | None
    status: ExecutionStatus
    idempotency_key: str | None
    code_revision: str
    worker_id: str | None
    attempt: int
    parameters: dict[str, Any]
    result_summary: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ExecutionListResponse(BaseModel):
    executions: list[ExecutionResponse]


class SpecificationResponse(BaseModel):
    id: UUID
    kind: SpecificationKind
    schema_version: int
    configuration: dict[str, Any]
    configuration_hash: str
    created_at: datetime


class ArtifactResponse(BaseModel):
    id: UUID
    kind: ArtifactKind
    storage_type: ArtifactStorageType
    storage_key: str | None
    content_sha256: str | None
    manifest: dict[str, Any] | None
    manifest_hash: str | None
    media_type: str | None
    byte_size: int | None
    created_at: datetime


class ArtifactLinkResponse(BaseModel):
    role: str
    position: int
    artifact: ArtifactResponse


class ExecutionLineageResponse(BaseModel):
    execution: ExecutionResponse
    specification: SpecificationResponse | None
    inputs: list[ArtifactLinkResponse]
    outputs: list[ArtifactLinkResponse]
