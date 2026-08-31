from dataclasses import replace
from uuid import UUID

from modules.projects.contracts.project_repo_contract import ProjectRepositoryContract
from modules.projects.models.project_model import (
    DefaultProjectDeletionError,
    ProjectAccess,
    ProjectNotFoundError,
    ProjectPermissionError,
    ProjectRole,
)


class ProjectService:
    def __init__(self, repository: ProjectRepositoryContract) -> None:
        self.repository = repository

    async def create(self, user_id: UUID, name: str, description: str | None) -> ProjectAccess:
        return ProjectAccess(
            await self.repository.create(user_id, name.strip(), description), ProjectRole.OWNER
        )

    async def list(self, user_id: UUID) -> list[ProjectAccess]:
        return await self.repository.list_for_user(user_id)

    async def get(self, project_id: UUID, user_id: UUID) -> ProjectAccess:
        access = await self.repository.get_access(project_id, user_id)
        if not access:
            raise ProjectNotFoundError
        return access

    async def update(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str | None,
        description: str | None,
        update_description: bool,
    ) -> ProjectAccess:
        access = await self.get(project_id, user_id)
        if access.role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise ProjectPermissionError
        project = await self.repository.update(
            project_id, name.strip() if name else None, description, update_description
        )
        project = replace(project, is_default=access.project.is_default)
        return ProjectAccess(project, access.role)

    async def delete(self, project_id: UUID, user_id: UUID) -> None:
        access = await self.get(project_id, user_id)
        if access.role is not ProjectRole.OWNER:
            raise ProjectPermissionError
        if access.project.is_default:
            raise DefaultProjectDeletionError
        await self.repository.delete(project_id)
