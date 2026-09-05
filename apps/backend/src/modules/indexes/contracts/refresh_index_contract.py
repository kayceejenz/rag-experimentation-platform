from uuid import UUID

from pydantic import BaseModel


class RefreshIndexRequest(BaseModel):
    knowledge_base_id: UUID
