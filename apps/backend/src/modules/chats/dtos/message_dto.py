
from dataclasses import Field
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from modules.chats.dtos.citation_dto import CitationResponse
from modules.chats.models.message_model import MessageRole


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=12000)

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    citations: list[CitationResponse]
    created_at: datetime

class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
