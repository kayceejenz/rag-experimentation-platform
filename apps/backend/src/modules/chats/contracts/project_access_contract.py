from typing import Protocol
from uuid import UUID

from modules.projects.models.project_model import ProjectAccess


class ProjectAccessContract(Protocol):
    def get(self, project_id: UUID, user_id: UUID) -> ProjectAccess: ...
