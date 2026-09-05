from uuid import UUID

from modules.knowledge_bases.models.knowledge_base_model import (
    KnowledgeBase,
    KnowledgeBaseNotFoundError,
)


class KnowledgeBaseService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def get(self, knowledge_base_id: UUID, user_id: UUID) -> KnowledgeBase:
        knowledge_base = self.repository.get_for_user(knowledge_base_id, user_id)
        if not knowledge_base:
            raise KnowledgeBaseNotFoundError
        return knowledge_base

    def get_for_project(self, project_id: UUID, user_id: UUID) -> KnowledgeBase:
        knowledge_base = self.repository.get_for_project(project_id, user_id)
        if knowledge_base is None:
            raise KnowledgeBaseNotFoundError
        return knowledge_base
