from collections.abc import Mapping
from typing import Any
from uuid import UUID

from modules.core.contracts.specification_contract import (
    SpecificationRepositoryContract,
    SpecificationSchemaRegistry,
)
from modules.core.helpers.canonical_json import canonical_json
from modules.core.models.error_model import UnsupportedSpecificationSchemaError
from modules.core.models.specification_model import Specification, SpecificationKind


class SpecificationService:
    def __init__(
        self,
        repository: SpecificationRepositoryContract,
        schemas: SpecificationSchemaRegistry,
    ) -> None:
        self.repository = repository
        self.schemas = schemas

    def register(
        self,
        project_id: UUID,
        created_by: UUID | None,
        kind: SpecificationKind,
        schema_version: int,
        configuration: Mapping[str, Any],
    ) -> Specification:
        normalizer = self.schemas.normalizer_for(kind, schema_version)
        if normalizer is None:
            raise UnsupportedSpecificationSchemaError(
                f"Unsupported specification schema {kind.value}@{schema_version}"
            )
        normalized = normalizer(configuration)
        identity = canonical_json(normalized)
        return self.repository.register(
            Specification(
                project_id=project_id,
                kind=kind,
                schema_version=schema_version,
                configuration=identity.value,
                configuration_hash=identity.sha256,
                created_by=created_by,
            )
        )
