from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    project_id: UUID
    chat_id: UUID
    name: str
    created_at: datetime
