from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import current_user, lineage_service
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.core.dtos.lineage_dto import (
    ExecutionLineageResponse,
    ExecutionListResponse,
    ExecutionResponse,
)
from modules.core.services.lineage_service import ExecutionNotFoundError, LineageService
from modules.projects.models.project_model import ProjectNotFoundError, ProjectPermissionError

router = APIRouter(prefix="/projects/{project_id}/executions", tags=["execution lineage"])


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[LineageService, Depends(lineage_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ExecutionListResponse:
    try:
        executions = await service.list_executions(project_id, user.id, limit)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found") from None
    except ProjectPermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient run permissions") from None
    return ExecutionListResponse(
        executions=[ExecutionResponse.model_validate(item, from_attributes=True) for item in executions]
    )


@router.get("/{execution_id}", response_model=ExecutionLineageResponse)
async def get_execution(
    project_id: UUID,
    execution_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[LineageService, Depends(lineage_service)],
) -> ExecutionLineageResponse:
    try:
        lineage = await service.get_execution(project_id, execution_id, user.id)
    except (ProjectNotFoundError, ExecutionNotFoundError):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Project or execution not found"
        ) from None
    except ProjectPermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient run permissions") from None
    return ExecutionLineageResponse.model_validate(lineage, from_attributes=True)
