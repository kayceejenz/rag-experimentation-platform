from typing import Protocol
from uuid import UUID

from modules.knowledge_bots.models.models import KnowledgeBot, KnowledgeBotStatus


class KnowledgeBotRepositoryContract(Protocol):
    async def create(
        self, project_id: UUID, created_by: UUID, name: str, description: str | None
    ) -> KnowledgeBot: ...

    async def get(self, bot_id: UUID, user_id: UUID) -> KnowledgeBot | None: ...

    async def list_for_project(
        self, project_id: UUID, user_id: UUID
    ) -> list[KnowledgeBot]: ...

    async def update(
        self,
        bot_id: UUID,
        name: str | None,
        description: str | None,
        update_description: bool,
        bot_status: KnowledgeBotStatus | None,
    ) -> KnowledgeBot: ...

    async def delete(self, bot_id: UUID) -> None: ...
