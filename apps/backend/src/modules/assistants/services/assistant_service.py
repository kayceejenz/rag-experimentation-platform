from uuid import UUID

from modules.assistants.contracts.assistant_repo_contract import (
    AssistantRepositoryContract,
)
from modules.assistants.models.assistant_model import (
    Assistant,
    AssistantNotFoundError,
    AssistantPermissionError,
    AssistantStatus,
)
from modules.projects.models.project_model import ProjectRole
from modules.projects.services.project_service import ProjectService


class AssistantService:
    def __init__(
        self, repository: AssistantRepositoryContract, projects: ProjectService
    ) -> None:
        self.repository = repository
        self.projects = projects

    async def create(
        self,
        project_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
        experiment_variant_run_id: UUID,
    ) -> tuple[Assistant, ProjectRole]:
        access = await self.projects.require_permission(
            project_id, user_id, "assistants", "manage"
        )
        assistant = await self.repository.create(
            project_id,
            user_id,
            name.strip(),
            self._description(description),
            experiment_variant_run_id,
        )
        return assistant, access.role

    async def candidates(self, project_id: UUID, user_id: UUID) -> list[dict]:
        await self.projects.require_permission(project_id, user_id, "assistants")
        return await self.repository.completed_run_candidates(project_id)

    async def lineage(self, assistant_id: UUID, user_id: UUID) -> dict:
        assistant, _ = await self.get(assistant_id, user_id)
        result = await self.repository.lineage(assistant.id, assistant.project_id)
        if not result:
            raise AssistantNotFoundError
        return result

    async def runtime_configuration(self, assistant_id: UUID, user_id: UUID) -> dict:
        assistant, _ = await self.get(assistant_id, user_id)
        result = await self.repository.runtime_configuration(
            assistant.id, assistant.project_id
        )
        if not result:
            raise ValueError("The assistant has no active experiment-backed revision")
        return result

    async def list(
        self, project_id: UUID, user_id: UUID
    ) -> tuple[list[Assistant], ProjectRole]:
        access = await self.projects.require_permission(
            project_id, user_id, "assistants"
        )
        return await self.repository.list_for_project(project_id, user_id), access.role

    async def get(
        self, assistant_id: UUID, user_id: UUID
    ) -> tuple[Assistant, ProjectRole]:
        assistant = await self.repository.get(assistant_id, user_id)
        if not assistant:
            raise AssistantNotFoundError
        access = await self.projects.require_permission(
            assistant.project_id, user_id, "assistants"
        )
        return assistant, access.role

    async def update(
        self,
        assistant_id: UUID,
        user_id: UUID,
        name: str | None,
        description: str | None,
        update_description: bool,
        assistant_status: AssistantStatus | None,
    ) -> tuple[Assistant, ProjectRole]:
        assistant, role = await self.get(assistant_id, user_id)
        await self.projects.require_permission(
            assistant.project_id, user_id, "assistants", "manage"
        )
        updated = await self.repository.update(
            assistant.id,
            name.strip() if name else None,
            self._description(description),
            update_description,
            assistant_status,
        )
        return updated, role

    async def delete(self, assistant_id: UUID, user_id: UUID) -> None:
        assistant, _ = await self.get(assistant_id, user_id)
        await self.projects.require_permission(
            assistant.project_id, user_id, "assistants", "manage"
        )
        await self.repository.delete(assistant.id)

    @staticmethod
    def _description(description: str | None) -> str | None:
        return description.strip() if description and description.strip() else None

    @staticmethod
    def _require_editor(role: ProjectRole) -> None:
        if role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise AssistantPermissionError
