import unittest
from collections.abc import Callable, Mapping
from typing import Any
from uuid import UUID, uuid4

from modules.core.models.error_model import UnsupportedSpecificationSchemaError
from modules.core.models.specification_model import Specification, SpecificationKind
from modules.core.services.specification_service import SpecificationService


class InMemorySpecificationRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[UUID, SpecificationKind, int, str], Specification] = {}

    def register(self, specification: Specification) -> Specification:
        key = (
            specification.project_id,
            specification.kind,
            specification.schema_version,
            specification.configuration_hash,
        )
        return self.records.setdefault(key, specification)

    def get(self, specification_id: UUID, project_id: UUID) -> Specification | None:
        return next(
            (
                item
                for item in self.records.values()
                if item.id == specification_id and item.project_id == project_id
            ),
            None,
        )


class TestSchemaRegistry:
    def __init__(
        self,
        schemas: dict[
            tuple[SpecificationKind, int],
            Callable[[Mapping[str, Any]], dict[str, Any]],
        ],
    ) -> None:
        self.schemas = schemas

    def normalizer_for(self, kind: SpecificationKind, schema_version: int):
        return self.schemas.get((kind, schema_version))


def embedding_v1(configuration: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "provider": str(configuration["provider"]),
        "model": str(configuration["model"]),
        "dimensions": int(configuration.get("dimensions", 768)),
        "distance_metric": str(configuration.get("distance_metric", "cosine")),
    }


class SpecificationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemorySpecificationRepository()
        self.service = SpecificationService(
            self.repository,
            TestSchemaRegistry({(SpecificationKind.EMBEDDING, 1): embedding_v1}),
        )
        self.project_id = uuid4()
        self.user_id = uuid4()

    def test_defaults_are_expanded_before_identity_is_calculated(self) -> None:
        implicit = self.service.register(
            self.project_id,
            self.user_id,
            SpecificationKind.EMBEDDING,
            1,
            {"provider": "gemini", "model": "embedding-model"},
        )
        explicit = self.service.register(
            self.project_id,
            self.user_id,
            SpecificationKind.EMBEDDING,
            1,
            {
                "model": "embedding-model",
                "provider": "gemini",
                "dimensions": 768,
                "distance_metric": "cosine",
            },
        )

        self.assertEqual(implicit.id, explicit.id)
        self.assertEqual(implicit.configuration, explicit.configuration)
        self.assertEqual(1, len(self.repository.records))

    def test_identity_is_scoped_to_project(self) -> None:
        configuration = {"provider": "gemini", "model": "embedding-model"}
        first = self.service.register(
            self.project_id,
            self.user_id,
            SpecificationKind.EMBEDDING,
            1,
            configuration,
        )
        second = self.service.register(
            uuid4(),
            self.user_id,
            SpecificationKind.EMBEDDING,
            1,
            configuration,
        )

        self.assertNotEqual(first.id, second.id)

    def test_unknown_schema_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            UnsupportedSpecificationSchemaError,
            "embedding@2",
        ):
            self.service.register(
                self.project_id,
                self.user_id,
                SpecificationKind.EMBEDDING,
                2,
                {"provider": "gemini", "model": "embedding-model"},
            )


if __name__ == "__main__":
    unittest.main()
