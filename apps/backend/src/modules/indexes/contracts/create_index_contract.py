from uuid import UUID

from pydantic import BaseModel, Field


class CreateIndexRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    knowledge_base_id: UUID
    embedding_model_id: UUID
    chunking_strategy: str = "by_title"
    folder_ids: list[UUID] = Field(default_factory=list)
