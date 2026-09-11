from uuid import UUID

from modules.knowledge_bots.contracts.knowledge_bot_repo_contracts import (
    KnowledgeBotRepositoryContract,
)
from modules.knowledge_bots.models.models import (
    KnowledgeBot,
    KnowledgeBotNotFoundError,
    KnowledgeBotPermissionError,
    KnowledgeBotStatus,
)
from modules.projects.models.project_model import ProjectRole
from modules.projects.services.project_service import ProjectService


class KnowledgeBotService:
    def __init__(
        self, repository: KnowledgeBotRepositoryContract, projects: ProjectService
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
    ) -> tuple[KnowledgeBot, ProjectRole]:
        access = await self.projects.require_permission(
            project_id, user_id, "assistants", "manage"
        )
        bot = await self.repository.create(
            project_id,
            user_id,
            name.strip(),
            self._description(description),
            experiment_variant_run_id,
        )
        return bot, access.role

    async def candidates(self, project_id: UUID, user_id: UUID) -> list[dict]:
        await self.projects.require_permission(project_id, user_id, "assistants")
        return await self.repository.completed_run_candidates(project_id)

    async def lineage(self, bot_id: UUID, user_id: UUID) -> dict:
        bot, _ = await self.get(bot_id, user_id)
        result = await self.repository.lineage(bot.id, bot.project_id)
        if not result:
            raise KnowledgeBotNotFoundError
        return result

    async def runtime_configuration(self, bot_id: UUID, user_id: UUID) -> dict:
        bot, _ = await self.get(bot_id, user_id)
        result = await self.repository.runtime_configuration(bot.id, bot.project_id)
        if not result:
            raise ValueError("The assistant has no active experiment-backed revision")
        return result

    async def list(
        self, project_id: UUID, user_id: UUID
    ) -> tuple[list[KnowledgeBot], ProjectRole]:
        access = await self.projects.require_permission(
            project_id, user_id, "assistants"
        )
        return await self.repository.list_for_project(project_id, user_id), access.role

    async def get(
        self, bot_id: UUID, user_id: UUID
    ) -> tuple[KnowledgeBot, ProjectRole]:
        bot = await self.repository.get(bot_id, user_id)
        if not bot:
            raise KnowledgeBotNotFoundError
        access = await self.projects.require_permission(
            bot.project_id, user_id, "assistants"
        )
        return bot, access.role

    async def update(
        self,
        bot_id: UUID,
        user_id: UUID,
        name: str | None,
        description: str | None,
        update_description: bool,
        bot_status: KnowledgeBotStatus | None,
    ) -> tuple[KnowledgeBot, ProjectRole]:
        bot, role = await self.get(bot_id, user_id)
        await self.projects.require_permission(
            bot.project_id, user_id, "assistants", "manage"
        )
        updated = await self.repository.update(
            bot.id,
            name.strip() if name else None,
            self._description(description),
            update_description,
            bot_status,
        )
        return updated, role

    async def delete(self, bot_id: UUID, user_id: UUID) -> None:
        (bot,) = await self.get(bot_id, user_id)
        await self.projects.require_permission(
            bot.project_id, user_id, "assistants", "manage"
        )
        await self.repository.delete(bot.id)

    @staticmethod
    def _description(description: str | None) -> str | None:
        return description.strip() if description and description.strip() else None

    @staticmethod
    def _require_editor(role: ProjectRole) -> None:
        if role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise KnowledgeBotPermissionError
