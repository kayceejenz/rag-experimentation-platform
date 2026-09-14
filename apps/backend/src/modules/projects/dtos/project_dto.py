from datetime import datetime
from uuid import UUID

from modules.core.dtos.lineage_dto import ExecutionResponse
from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    owner_id: UUID
    name: str
    description: str | None
    role: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    permissions: dict[str, dict[str, bool]]


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


class WorkspaceProjectStatusResponse(BaseModel):
    project_id: UUID
    index_count: int
    active_runs: int
    failed_runs: int
    last_activity: datetime | None


class WorkspaceExecutionResponse(ExecutionResponse):
    project_name: str


class WorkspaceOverviewResponse(BaseModel):
    projects: list[ProjectResponse]
    index_count: int
    ready_indexes: int
    building_indexes: int
    active_assistants: int
    failed_runs: int
    project_statuses: list[WorkspaceProjectStatusResponse]
    recent_executions: list[WorkspaceExecutionResponse]


class FeaturePermission(BaseModel):
    view: bool
    manage: bool


class ProjectMemberResponse(BaseModel):
    user_id: UUID
    email: str
    display_name: str | None
    role: str
    joined_at: datetime
    permissions: dict[str, FeaturePermission]


class ProjectMemberListResponse(BaseModel):
    members: list[ProjectMemberResponse]


class AddProjectMemberRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    permissions: dict[str, FeaturePermission]


class UpdateProjectMemberAccessRequest(BaseModel):
    permissions: dict[str, FeaturePermission]
