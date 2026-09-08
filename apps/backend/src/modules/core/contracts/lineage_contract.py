from typing import Protocol
from uuid import UUID

from modules.core.models.execution_model import Execution
from modules.core.models.lineage_model import ExecutionLineage


class LineageRepositoryContract(Protocol):
    async def list_executions(
        self, project_id: UUID, limit: int
    ) -> list[Execution]: ...

    async def get_execution(
        self, project_id: UUID, execution_id: UUID
    ) -> ExecutionLineage | None: ...
