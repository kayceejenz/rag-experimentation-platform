from uuid import UUID

from modules.projects.contracts.project_repo_contract import ProjectRepositoryContract
from modules.projects.models.project_model import (
    ProjectAccess,
    ProjectNotFoundError,
    ProjectPermissionError,
    ProjectRole,
)


class ProjectService:
    def __init__(self, repository: ProjectRepositoryContract) -> None:
        self.repository = repository

    def create(self, user_id: UUID, name: str, description: str | None) -> ProjectAccess:
        return ProjectAccess(
            self.repository.create(user_id, name.strip(), description), ProjectRole.OWNER
        )

    def list(self, user_id: UUID) -> list[ProjectAccess]:
        return self.repository.list_for_user(user_id)

    def get(self, project_id: UUID, user_id: UUID) -> ProjectAccess:
        access = self.repository.get_access(project_id, user_id)
        if not access:
            raise ProjectNotFoundError
        return access

    def update(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str | None,
        description: str | None,
        update_description: bool,
    ) -> ProjectAccess:
        access = self.get(project_id, user_id)
        if access.role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise ProjectPermissionError
        project = self.repository.update(
            project_id, name.strip() if name else None, description, update_description
        )
        return ProjectAccess(project, access.role)

    def delete(self, project_id: UUID, user_id: UUID) -> None:
        access = self.get(project_id, user_id)
        if access.role is not ProjectRole.OWNER:
            raise ProjectPermissionError
        self.repository.delete(project_id)
