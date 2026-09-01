from datetime import datetime
from uuid import UUID

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
