import asyncio
from uuid import UUID

from modules.core.contracts.lineage_contract import LineageRepositoryContract
from modules.core.models.execution_model import Execution
from modules.core.models.lineage_model import ExecutionLineage
from modules.projects.services.project_service import ProjectService


class ExecutionNotFoundError(Exception):
    pass


class LineageService:
    def __init__(
        self,
        repository: LineageRepositoryContract,
        projects: ProjectService,
    ) -> None:
        self.repository = repository
        self.projects = projects

    async def list_executions(
        self, project_id: UUID, user_id: UUID, limit: int
    ) -> list[Execution]:
        await self.projects.get(project_id, user_id)
        return await asyncio.to_thread(
            self.repository.list_executions, project_id, limit
        )

    async def get_execution(
        self, project_id: UUID, execution_id: UUID, user_id: UUID
    ) -> ExecutionLineage:
        await self.projects.get(project_id, user_id)
        lineage = await asyncio.to_thread(
            self.repository.get_execution, project_id, execution_id
        )
        if lineage is None:
            raise ExecutionNotFoundError
        return lineage
