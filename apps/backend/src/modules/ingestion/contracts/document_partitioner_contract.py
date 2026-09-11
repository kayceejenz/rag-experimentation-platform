from pathlib import Path
from typing import Protocol

from modules.ingestion.models.document_element_model import DocumentElement


class DocumentPartitioner(Protocol):
    def partition(self, path: Path) -> list[DocumentElement]: ...
