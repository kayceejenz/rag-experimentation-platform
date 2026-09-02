from datetime import datetime
from uuid import UUID

from modules.knowledge_bots.models.models import KnowledgeBotStatus
from pydantic import BaseModel, ConfigDict, Field


class CreateKnowledgeBotRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class UpdateKnowledgeBotRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    status: KnowledgeBotStatus | None = None


class KnowledgeBotResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by: UUID
    name: str
    description: str | None
    status: KnowledgeBotStatus
    role: str
    created_at: datetime
    updated_at: datetime


class KnowledgeBotListResponse(BaseModel):
    assistants: list[KnowledgeBotResponse]
