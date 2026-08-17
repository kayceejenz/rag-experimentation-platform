from uuid import UUID

from pydantic import BaseModel


class CitationResponse(BaseModel):
    source_id: UUID
    chunk_id: UUID
    source_filename: str
    excerpt: str
    page_number: int | None
    element_ids: list[str]