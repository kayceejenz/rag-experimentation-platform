from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Citation:
    source_id: UUID
    chunk_id: UUID
    source_filename: str
    excerpt: str
    page_number: int | None = None
    element_ids: tuple[str, ...] = ()
    coordinates: tuple[dict[str, Any], ...] = ()
