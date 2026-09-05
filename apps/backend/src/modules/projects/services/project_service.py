from dataclasses import replace
from uuid import UUID

from modules.projects.contracts.project_repo_contract import ProjectRepositoryContract
from modules.projects.models.project_model import (
    DefaultProjectDeletionError,
    ProjectAccess,
    ProjectMemberConflictError,
    ProjectNotFoundError,
    ProjectPermissionError,
    ProjectRole,
)


class ProjectService:
    FEATURES = {
        "knowledge",
        "indexes",
        "experiments",
        "benchmarks",
        "prompts",
        "assistants",
        "runs",
        "settings",
    }

    def __init__(self, repository: ProjectRepositoryContract) -> None:
        self.repository = repository

    async def create(
        self, user_id: UUID, name: str, description: str | None
    ) -> ProjectAccess:
        return ProjectAccess(
            await self.repository.create(user_id, name.strip(), description),
            ProjectRole.OWNER,
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
        if not await self.repository.has_permission(
            project_id, user_id, "settings", "manage"
        ):
            raise ProjectPermissionError
        project = await self.repository.update(
            project_id, name.strip() if name else None, description, update_description
        )
        project = replace(project, is_default=access.project.is_default)
        return ProjectAccess(project, access.role, access.permissions)

    async def delete(self, project_id: UUID, user_id: UUID) -> None:
        access = await self.get(project_id, user_id)
        if access.role is not ProjectRole.OWNER:
            raise ProjectPermissionError
        if access.project.is_default:
            raise DefaultProjectDeletionError
        await self.repository.delete(project_id)

    async def require_permission(
        self, project_id, user_id, feature, action="view"
    ) -> ProjectAccess:
        access = await self.get(project_id, user_id)
        if not await self.repository.has_permission(
            project_id, user_id, feature, action
        ):
            raise ProjectPermissionError
        return access

    async def members(self, project_id, user_id):
        await self.require_permission(project_id, user_id, "settings")
        return await self.repository.list_members(project_id)

    async def add_member(self, project_id, user_id, email, permissions):
        await self._require_owner(project_id, user_id)
        normalized = self._permissions(permissions)
        result = await self.repository.add_member(
            project_id, email.strip().lower(), normalized
        )
        if result is None:
            raise ProjectNotFoundError
        if result is False:
            raise ProjectMemberConflictError

    async def update_member_access(self, project_id, user_id, member_id, permissions):
        await self._require_owner(project_id, user_id)
        if not await self.repository.update_member_permissions(
            project_id, member_id, self._permissions(permissions)
        ):
            raise ProjectNotFoundError

    async def remove_member(self, project_id, user_id, member_id):
        await self._require_owner(project_id, user_id)
        if not await self.repository.remove_member(project_id, member_id):
            raise ProjectNotFoundError

    async def _require_owner(self, project_id, user_id):
        access = await self.get(project_id, user_id)
        if access.role is not ProjectRole.OWNER:
            raise ProjectPermissionError

    def _permissions(self, permissions):
        if set(permissions) != self.FEATURES:
            raise ValueError("Permissions must be supplied for every project feature")
        return {
            feature: {"view": value.view or value.manage, "manage": value.manage}
            for feature, value in permissions.items()
        }
