from pathlib import Path
from typing import Protocol
from uuid import UUID

from modules.ingestion.models.ingestion_model import Chunk, DocumentElement


class DocumentPartitioner(Protocol):
    def partition(self, path: Path) -> list[DocumentElement]: ...


class ElementWriter(Protocol):
    def get_for_source(self, source_version_id: UUID) -> list[DocumentElement]: ...

    def replace_for_source(
        self, source_version_id: UUID, elements: list[DocumentElement]
    ) -> None: ...


class ElementAssetStorage(Protocol):
    def save_base64(
        self, source_id: UUID, element_id: str, payload: str, content_type: str
    ) -> str: ...


class ChunkWriter(Protocol):
    def replace_for_source(
        self,
        project_id: UUID,
        source_version_id: UUID,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None: ...


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
