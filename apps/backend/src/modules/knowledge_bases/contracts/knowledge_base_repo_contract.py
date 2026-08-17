from typing import Protocol
from uuid import UUID

from modules.knowledge_bases.models.knowledge_base_model import KnowledgeBase


class KnowledgeBaseRepository(Protocol):
    def add(self, knowledge_base: KnowledgeBase) -> None: ...
    def get_for_chat(self, chat_id: UUID) -> KnowledgeBase | None: ...
