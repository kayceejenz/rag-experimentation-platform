from uuid import UUID

from modules.knowledge_bots.contracts import KnowledgeBotRepositoryContract
from modules.knowledge_bots.models import (
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
    ) -> tuple[KnowledgeBot, ProjectRole]:
        access = await self.projects.require_permission(project_id, user_id, "assistants", "manage")
        bot = await self.repository.create(
            project_id, user_id, name.strip(), self._description(description)
        )
        return bot, access.role

    async def list(
        self, project_id: UUID, user_id: UUID
    ) -> tuple[list[KnowledgeBot], ProjectRole]:
        access = await self.projects.require_permission(project_id, user_id, "assistants")
        return await self.repository.list_for_project(project_id, user_id), access.role

    async def get(self, bot_id: UUID, user_id: UUID) -> tuple[KnowledgeBot, ProjectRole]:
        bot = await self.repository.get(bot_id, user_id)
        if not bot:
            raise KnowledgeBotNotFoundError
        access = await self.projects.require_permission(bot.project_id, user_id, "assistants")
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
        await self.projects.require_permission(bot.project_id, user_id, "assistants", "manage")
        updated = await self.repository.update(
            bot.id,
            name.strip() if name else None,
            self._description(description),
            update_description,
            bot_status,
        )
        return updated, role

    async def delete(self, bot_id: UUID, user_id: UUID) -> None:
        bot, role = await self.get(bot_id, user_id)
        await self.projects.require_permission(bot.project_id, user_id, "assistants", "manage")
        await self.repository.delete(bot.id)

    @staticmethod
    def _description(description: str | None) -> str | None:
        return description.strip() if description and description.strip() else None

    @staticmethod
    def _require_editor(role: ProjectRole) -> None:
        if role not in {ProjectRole.OWNER, ProjectRole.EDITOR}:
            raise KnowledgeBotPermissionError
