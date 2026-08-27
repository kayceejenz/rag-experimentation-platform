from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.chats.models.chat_model import ChatStatus
from modules.chats.models.message_model import MessageRole


class CreateChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(default="New chat", min_length=1, max_length=240)


class UpdateChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=240)
    status: ChatStatus | None = None


class ChatResponse(BaseModel):
    id: UUID
    bot_id: UUID
    project_id: UUID
    created_by: UUID
    knowledge_base_id: UUID
    title: str
    status: ChatStatus
    role: str
    created_at: datetime
    updated_at: datetime


class ChatListResponse(BaseModel):
    chats: list[ChatResponse]


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=12000)


class CitationResponse(BaseModel):
    source_id: UUID | None = None
    chunk_id: UUID | None = None
    source_filename: str
    excerpt: str
    page_number: int | None
    element_ids: list[str]


class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    citations: list[CitationResponse]
    created_at: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
