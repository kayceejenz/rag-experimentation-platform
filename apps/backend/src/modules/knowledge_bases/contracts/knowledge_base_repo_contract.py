from typing import Protocol
from uuid import UUID

from modules.knowledge_bases.models.knowledge_base_model import KnowledgeBase


class KnowledgeBaseRepository(Protocol):
    def get_for_user(
        self, knowledge_base_id: UUID, user_id: UUID
    ) -> KnowledgeBase | None: ...
    def get_for_project(
        self, project_id: UUID, user_id: UUID
    ) -> KnowledgeBase | None: ...
