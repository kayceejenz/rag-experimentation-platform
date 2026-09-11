from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Chunk:
    knowledge_base_id: UUID
    source_id: UUID
    text: str
    position: int
    element_ids: tuple[str, ...]
    page_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
