from typing import Protocol
from uuid import UUID

from modules.assistants.models.assistant_model import Assistant, AssistantStatus


class AssistantRepositoryContract(Protocol):
    async def create(
        self,
        project_id: UUID,
        created_by: UUID,
        name: str,
        description: str | None,
        experiment_variant_run_id: UUID,
    ) -> Assistant: ...

    async def completed_run_candidates(self, project_id: UUID) -> list[dict]: ...

    async def lineage(self, assistant_id: UUID, project_id: UUID) -> dict | None: ...

    async def runtime_configuration(
        self, assistant_id: UUID, project_id: UUID
    ) -> dict | None: ...

    async def get(self, assistant_id: UUID, user_id: UUID) -> Assistant | None: ...

    async def list_for_project(
        self, project_id: UUID, user_id: UUID
    ) -> list[Assistant]: ...

    async def update(
        self,
        assistant_id: UUID,
        name: str | None,
        description: str | None,
        update_description: bool,
        assistant_status: AssistantStatus | None,
    ) -> Assistant: ...

    async def delete(self, assistant_id: UUID) -> None: ...
