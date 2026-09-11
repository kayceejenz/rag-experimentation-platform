import unittest
from uuid import UUID, uuid4

from modules.core.models.artifact_model import (
    Artifact,
    ArtifactKind,
    ArtifactStorageType,
)
from modules.core.services.artifact_service import ArtifactService


class InMemoryArtifactRepository:
    def __init__(self) -> None:
        self.records: dict[tuple[UUID, ArtifactKind, str], Artifact] = {}

    def register(self, artifact: Artifact) -> Artifact:
        digest = artifact.content_sha256 or artifact.manifest_hash
        assert digest is not None
        return self.records.setdefault(
            (artifact.project_id, artifact.kind, digest), artifact
        )

    def get(self, artifact_id: UUID, project_id: UUID) -> Artifact | None:
        return next(
            (
                artifact
                for artifact in self.records.values()
                if artifact.id == artifact_id and artifact.project_id == project_id
            ),
            None,
        )


class ArtifactServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryArtifactRepository()
        self.service = ArtifactService(self.repository)
        self.project_id = uuid4()
        self.user_id = uuid4()

    def test_content_identity_deduplicates_within_project_and_kind(self) -> None:
        digest = "a" * 64
        first = self.service.register_content(
            self.project_id,
            self.user_id,
            ArtifactKind.SOURCE,
            ArtifactStorageType.OBJECT,
            digest,
            storage_key="sources/first.pdf",
        )
        second = self.service.register_content(
            self.project_id,
            self.user_id,
            ArtifactKind.SOURCE,
            ArtifactStorageType.OBJECT,
            digest,
            storage_key="sources/copy.pdf",
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(1, len(self.repository.records))

    def test_manifest_identity_is_independent_of_key_order(self) -> None:
        first = self.service.register_manifest(
            self.project_id,
            self.user_id,
            ArtifactKind.CHUNK_DATASET,
            {"table": "chunks", "partition": {"end": 20, "start": 10}},
        )
        second = self.service.register_manifest(
            self.project_id,
            self.user_id,
            ArtifactKind.CHUNK_DATASET,
            {"partition": {"start": 10, "end": 20}, "table": "chunks"},
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.manifest_hash, second.manifest_hash)

    def test_same_content_is_distinct_across_projects(self) -> None:
        digest = "b" * 64
        first = self.service.register_content(
            self.project_id,
            self.user_id,
            ArtifactKind.REPORT,
            ArtifactStorageType.EXTERNAL,
            digest,
        )
        second = self.service.register_content(
            uuid4(),
            self.user_id,
            ArtifactKind.REPORT,
            ArtifactStorageType.EXTERNAL,
            digest,
        )

        self.assertNotEqual(first.id, second.id)

    def test_object_artifact_requires_storage_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "storage_key"):
            self.service.register_content(
                self.project_id,
                self.user_id,
                ArtifactKind.SOURCE,
                ArtifactStorageType.OBJECT,
                "c" * 64,
            )

    def test_invalid_hash_and_negative_size_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            self.service.register_content(
                self.project_id,
                self.user_id,
                ArtifactKind.REPORT,
                ArtifactStorageType.EXTERNAL,
                "not-a-digest",
            )
        with self.assertRaisesRegex(ValueError, "negative"):
            self.service.register_content(
                self.project_id,
                self.user_id,
                ArtifactKind.REPORT,
                ArtifactStorageType.EXTERNAL,
                "d" * 64,
                byte_size=-1,
            )


if __name__ == "__main__":
    unittest.main()
