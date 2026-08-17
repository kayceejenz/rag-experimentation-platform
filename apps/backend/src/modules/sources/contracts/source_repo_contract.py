from typing import Protocol
from uuid import UUID

from modules.sources.models.source_model import Source, SourceStatus


class SourceRepository(Protocol):
    def add(self, source: Source) -> None: ...
    def get(self, source_id: UUID) -> Source | None: ...
    def set_status(
        self, source_id: UUID, status: SourceStatus, error: str | None = None
    ) -> None: ...
