from collections.abc import Callable, Mapping
from typing import Any, Protocol
from uuid import UUID

from modules.core.models.specification_model import Specification, SpecificationKind


SpecificationNormalizer = Callable[[Mapping[str, Any]], dict[str, Any]]


class SpecificationRepositoryContract(Protocol):
    def register(self, specification: Specification) -> Specification: ...

    def get(self, specification_id: UUID, project_id: UUID) -> Specification | None: ...


class SpecificationSchemaRegistry(Protocol):
    def normalizer_for(
        self, kind: SpecificationKind, schema_version: int
    ) -> SpecificationNormalizer | None: ...
