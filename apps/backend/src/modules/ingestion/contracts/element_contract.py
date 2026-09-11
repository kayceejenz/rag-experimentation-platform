from typing import Protocol
from uuid import UUID

from modules.ingestion.models.document_element_model import DocumentElement


class ElementWriter(Protocol):
    def get_for_source(self, source_version_id: UUID) -> list[DocumentElement]: ...

    def replace_for_source(
        self, source_version_id: UUID, elements: list[DocumentElement]
    ) -> None: ...


class ElementAssetStorage(Protocol):
    def save_base64(
        self, source_id: UUID, element_id: str, payload: str, content_type: str
    ) -> str: ...
