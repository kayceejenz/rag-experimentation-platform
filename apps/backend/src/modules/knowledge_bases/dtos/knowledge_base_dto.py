from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by: UUID
    name: str
    created_at: datetime
