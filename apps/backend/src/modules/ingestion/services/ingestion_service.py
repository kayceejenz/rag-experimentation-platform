from dataclasses import replace
from pathlib import Path
from uuid import UUID

from modules.ingestion.contracts.ingestion_contract import (
    ChunkWriter,
    DocumentPartitioner,
    ElementAssetStorage,
    ElementWriter,
    Embedder,
)
from modules.ingestion.models.ingestion_model import Chunk, DocumentElement


class IngestSource:
    def __init__(
        self,
        partitioner: DocumentPartitioner,
        elements: ElementWriter,
        chunks: ChunkWriter,
        assets: ElementAssetStorage,
        embedder: Embedder,
    ) -> None:
        self._partitioner = partitioner
        self._elements = elements
        self._chunks = chunks
        self._assets = assets
        self._embedder = embedder

    def execute(
        self,
        project_id: UUID,
        source_id: UUID,
        source_version_id: UUID,
        knowledge_base_id: UUID,
        path: Path,
    ) -> tuple[int, int]:
        persisted_elements = self._elements.get_for_source(source_version_id)
        if not persisted_elements:
            elements = self._partitioner.partition(path)
            persisted_elements = [self._persist_asset(source_id, element) for element in elements]
            self._elements.replace_for_source(source_version_id, persisted_elements)
        chunks = [
            Chunk(
                source_id=source_id,
                knowledge_base_id=knowledge_base_id,
                text=self._searchable_text(element),
                position=position,
                element_ids=(element.element_id,),
                page_number=element.page_number,
                metadata={
                    "category": element.category,
                    "page_number": element.page_number,
                    "element_ids": [element.element_id],
                },
            )
            for position, element in enumerate(persisted_elements)
            if self._searchable_text(element).strip()
        ]
        embeddings = self._embedder.embed([chunk.text for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding provider returned the wrong number of vectors")
        self._chunks.replace_for_source(project_id, source_version_id, chunks, embeddings)
        return len(persisted_elements), len(chunks)

    def _persist_asset(self, source_id: UUID, element: DocumentElement) -> DocumentElement:
        if not element.image_payload:
            return element

        storage_key = self._assets.save_base64(
            source_id,
            element.element_id,
            element.image_payload,
            element.image_mime_type or "image/jpeg",
        )
        return replace(
            element,
            image_payload=None,
            metadata={**element.metadata, "image_storage_key": storage_key},
        )

    @staticmethod
    def _searchable_text(element: DocumentElement) -> str:
        return element.text
