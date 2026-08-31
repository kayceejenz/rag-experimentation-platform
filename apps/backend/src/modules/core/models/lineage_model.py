from dataclasses import dataclass

from modules.core.models.artifact_model import Artifact
from modules.core.models.execution_model import Execution
from modules.core.models.specification_model import Specification


@dataclass(frozen=True)
class ArtifactLink:
    role: str
    position: int
    artifact: Artifact


@dataclass(frozen=True)
class ExecutionLineage:
    execution: Execution
    specification: Specification | None
    inputs: tuple[ArtifactLink, ...]
    outputs: tuple[ArtifactLink, ...]
