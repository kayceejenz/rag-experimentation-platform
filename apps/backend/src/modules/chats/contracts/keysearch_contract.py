from typing import Protocol
from uuid import UUID

from modules.chats.models.retrieval_model import RetrievedChunk


class KnowledgeSearch(Protocol):
    def search(
        self, knowledge_base_id: UUID, query: str, limit: int = 8
    ) -> list[RetrievedChunk]: ...
