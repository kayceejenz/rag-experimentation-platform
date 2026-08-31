from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ChatStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Chat:
    id: UUID
    assistant_id: UUID
    project_id: UUID
    created_by: UUID
    title: str
    status: ChatStatus
    created_at: datetime
    updated_at: datetime
