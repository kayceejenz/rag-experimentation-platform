from typing import Protocol
from uuid import UUID

from modules.projects.models.project_model import ProjectAccess


class ProjectAccessContract(Protocol):
    async def get(self, project_id: UUID, user_id: UUID) -> ProjectAccess: ...
    async def require_permission(
        self, project_id: UUID, user_id: UUID, feature: str, action: str = "view"
    ) -> ProjectAccess: ...
