from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    source_id: UUID
    source_filename: str
    text: str
    score: float
    page_number: int | None
    element_ids: tuple[str, ...]
    coordinates: tuple[dict[str, Any], ...]
    metadata: dict[str, Any]
