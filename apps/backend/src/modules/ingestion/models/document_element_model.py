from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentElement:
    element_id: str
    text: str
    category: str
    page_number: int | None = None
    parent_id: str | None = None
    coordinates: dict[str, Any] | None = None
    table_html: str | None = None
    image_payload: str | None = None
    image_mime_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
