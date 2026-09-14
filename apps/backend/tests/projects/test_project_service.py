import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from modules.projects.models.project_model import (
    Project,
    ProjectAccess,
    ProjectPermissionError,
    ProjectRole,
)
from modules.projects.services.project_service import ProjectService


def project_access(
    role: ProjectRole, permissions: dict | None = None
) -> ProjectAccess:
    now = datetime.now(UTC)
    return ProjectAccess(
        project=Project(
            id=uuid4(),
            workspace_id=uuid4(),
            owner_id=uuid4(),
            name="Demo",
            description=None,
            created_at=now,
            updated_at=now,
        ),
        role=role,
        permissions=permissions or {},
    )


class ProjectServicePermissionTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_is_allowed_without_a_second_repository_query(self):
        repository = AsyncMock()
        access = project_access(ProjectRole.OWNER)
        repository.get_access.return_value = access

        result = await ProjectService(repository).require_permission(
            access.project.id, uuid4(), "settings", "manage"
        )

        self.assertEqual(result, access)
        repository.has_permission.assert_not_awaited()

    async def test_member_permission_is_read_from_loaded_access(self):
        repository = AsyncMock()
        access = project_access(
            ProjectRole.VIEWER,
            {"knowledge": {"view": True, "manage": False}},
        )
        repository.get_access.return_value = access
        service = ProjectService(repository)

        self.assertEqual(
            await service.require_permission(
                access.project.id, uuid4(), "knowledge"
            ),
            access,
        )
        with self.assertRaises(ProjectPermissionError):
            await service.require_permission(
                access.project.id, uuid4(), "knowledge", "manage"
            )
        repository.has_permission.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
