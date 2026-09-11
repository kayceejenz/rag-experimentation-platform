from typing import Protocol
from uuid import UUID

from modules.ingestion.models.chunk_element_model import Chunk


class ChunkWriter(Protocol):
    def replace_chunks(
        self,
        project_id: UUID,
        source_version_id: UUID,
        chunks: list[Chunk],
    ) -> None: ...

    def texts_for_source(self, source_version_id: UUID) -> list[str]: ...
    def replace_embeddings(
        self, source_version_id: UUID, embeddings: list[list[float]]
    ) -> None: ...
