from dataclasses import replace
from pathlib import Path
from uuid import UUID

from modules.ingestion.contracts.chunk_writer_contract import ChunkWriter
from modules.ingestion.contracts.document_partitioner_contract import (
    DocumentPartitioner,
)
from modules.ingestion.contracts.element_contract import (
    ElementAssetStorage,
    ElementWriter,
)
from modules.ingestion.contracts.embedder_contract import Embedder
from modules.ingestion.models.chunk_element_model import Chunk
from modules.ingestion.models.document_element_model import DocumentElement


class IngestSource:
    def __init__(
        self,
        partitioner: DocumentPartitioner,
        elements: ElementWriter,
        chunks: ChunkWriter,
        assets: ElementAssetStorage,
        embedder: Embedder | None = None,
    ) -> None:
        self._partitioner = partitioner
        self._elements = elements
        self._chunks = chunks
        self._assets = assets
        self._embedder = embedder

    def execute_chunking(
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
            persisted_elements = [
                self._persist_asset(source_id, element) for element in elements
            ]
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
        self._chunks.replace_chunks(project_id, source_version_id, chunks)
        return len(persisted_elements), len(chunks)

    def execute_indexing(self, source_version_id: UUID) -> int:
        if self._embedder is None:
            raise ValueError("An embedding provider is required for index building")
        texts = self._chunks.texts_for_source(source_version_id)
        embeddings = self._embedder.embed(texts)
        if len(embeddings) != len(texts):
            raise ValueError("Embedding provider returned the wrong number of vectors")
        self._chunks.replace_embeddings(source_version_id, embeddings)
        return len(texts)

    def _persist_asset(
        self, source_id: UUID, element: DocumentElement
    ) -> DocumentElement:
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
