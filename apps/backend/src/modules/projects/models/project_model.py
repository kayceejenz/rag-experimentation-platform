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
    owner_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ProjectAccess:
    project: Project
    role: ProjectRole


class ProjectNotFoundError(Exception):
    pass


class ProjectPermissionError(Exception):
    pass
