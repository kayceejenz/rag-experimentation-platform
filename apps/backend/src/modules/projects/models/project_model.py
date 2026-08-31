from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass(frozen=True)
class Project:
    id: UUID
    workspace_id: UUID
    owner_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    is_default: bool = False


@dataclass(frozen=True)
class ProjectAccess:
    project: Project
    role: ProjectRole


class ProjectNotFoundError(Exception):
    pass


class ProjectPermissionError(Exception):
    pass


class DefaultProjectDeletionError(Exception):
    pass
