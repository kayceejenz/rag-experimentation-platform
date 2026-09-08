import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from modules.core.models.execution_model import Execution, ExecutionKind
from modules.core.models.lineage_model import ExecutionLineage
from modules.core.services.lineage_service import ExecutionNotFoundError, LineageService
from modules.projects.models.project_model import ProjectNotFoundError


class LineageServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = MagicMock()
        self.repository.list_executions = AsyncMock()
        self.repository.get_execution = AsyncMock()
        self.projects = MagicMock()
        self.projects.require_permission = AsyncMock()
        self.service = LineageService(self.repository, self.projects)
        self.project_id = uuid4()
        self.user_id = uuid4()

    async def test_list_requires_project_membership(self) -> None:
        self.projects.require_permission.side_effect = ProjectNotFoundError

        with self.assertRaises(ProjectNotFoundError):
            await self.service.list_executions(self.project_id, self.user_id, 50)

        self.repository.list_executions.assert_not_awaited()

    async def test_list_is_scoped_to_authorized_project(self) -> None:
        execution = Execution(
            project_id=self.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
        )
        self.repository.list_executions.return_value = [execution]

        result = await self.service.list_executions(self.project_id, self.user_id, 25)

        self.projects.require_permission.assert_awaited_once_with(
            self.project_id, self.user_id, "runs"
        )
        self.repository.list_executions.assert_awaited_once_with(self.project_id, 25)
        self.assertEqual([execution], result)

    async def test_missing_execution_returns_domain_not_found(self) -> None:
        self.repository.get_execution.return_value = None

        with self.assertRaises(ExecutionNotFoundError):
            await self.service.get_execution(self.project_id, uuid4(), self.user_id)

    async def test_detail_returns_typed_lineage(self) -> None:
        execution = Execution(
            project_id=self.project_id,
            kind=ExecutionKind.INGESTION,
            code_revision="ragapp-backend@0.1.0",
        )
        lineage = ExecutionLineage(execution, None, (), ())
        self.repository.get_execution.return_value = lineage

        result = await self.service.get_execution(
            self.project_id, execution.id, self.user_id
        )

        self.assertEqual(lineage, result)
        self.repository.get_execution.assert_awaited_once_with(
            self.project_id, execution.id
        )


if __name__ == "__main__":
    unittest.main()
