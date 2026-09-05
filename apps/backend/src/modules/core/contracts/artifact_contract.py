from typing import Protocol
from uuid import UUID

from modules.core.models.artifact_model import Artifact


class ArtifactRepositoryContract(Protocol):
    def register(self, artifact: Artifact) -> Artifact: ...

    def get(self, artifact_id: UUID, project_id: UUID) -> Artifact | None: ...
