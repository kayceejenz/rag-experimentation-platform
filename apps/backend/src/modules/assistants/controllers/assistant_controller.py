from typing import Annotated
from uuid import UUID

from api.dependencies import assistant_service, current_user
from fastapi import APIRouter, Depends, HTTPException, Response, status
from modules.assistants.models.assistant_dto import (
    AssistantCandidateListResponse,
    AssistantLineageResponse,
    AssistantListResponse,
    AssistantResponse,
    CreateAssistantRequest,
    UpdateAssistantRequest,
)
from modules.assistants.models.assistant_model import (
    Assistant,
    AssistantNotFoundError,
    AssistantPermissionError,
)
from modules.assistants.services.assistant_service import AssistantService
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.projects.models.project_model import (
    ProjectNotFoundError,
    ProjectPermissionError,
)

router = APIRouter(tags=["assistants"])


def response(assistant: Assistant, role: str) -> AssistantResponse:
    return AssistantResponse(
        id=assistant.id,
        project_id=assistant.project_id,
        created_by=assistant.created_by,
        name=assistant.name,
        description=assistant.description,
        status=assistant.status,
        role=role,
        created_at=assistant.created_at,
        updated_at=assistant.updated_at,
        active_revision_version=assistant.active_revision_version,
        source_run_id=assistant.source_run_id,
        source_variant_run_id=assistant.source_variant_run_id,
        source_experiment_name=assistant.source_experiment_name,
        source_variant_name=assistant.source_variant_name,
    )


def translate(error: Exception) -> HTTPException:
    if isinstance(error, ValueError):
        return HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
    if isinstance(error, (AssistantNotFoundError, ProjectNotFoundError)):
        return HTTPException(
            status.HTTP_404_NOT_FOUND, "Assistant or project not found"
        )
    return HTTPException(
        status.HTTP_403_FORBIDDEN, "Insufficient assistant permissions"
    )


@router.post(
    "/projects/{project_id}/assistants",
    response_model=AssistantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assistant(
    project_id: UUID,
    body: CreateAssistantRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
):
    try:
        assistant, role = await service.create(
            project_id,
            user.id,
            body.name,
            body.description,
            body.experiment_variant_run_id,
        )
        return response(assistant, role.value)
    except (
        ProjectNotFoundError,
        ProjectPermissionError,
        AssistantPermissionError,
        ValueError,
    ) as error:
        raise translate(error) from None


@router.get(
    "/projects/{project_id}/assistant-candidates",
    response_model=AssistantCandidateListResponse,
)
async def assistant_candidates(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
):
    try:
        return AssistantCandidateListResponse(
            candidates=await service.candidates(project_id, user.id)
        )
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.get("/projects/{project_id}/assistants", response_model=AssistantListResponse)
async def list_assistants(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
):
    try:
        assistants, role = await service.list(project_id, user.id)
        return AssistantListResponse(
            assistants=[response(assistant, role.value) for assistant in assistants]
        )
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.get("/assistants/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
):
    try:
        assistant, role = await service.get(assistant_id, user.id)
        return response(assistant, role.value)
    except (
        AssistantNotFoundError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None


@router.get(
    "/assistants/{assistant_id}/lineage", response_model=AssistantLineageResponse
)
async def assistant_lineage(
    assistant_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
):
    try:
        return await service.lineage(assistant_id, user.id)
    except (
        AssistantNotFoundError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None


@router.patch("/assistants/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: UUID,
    body: UpdateAssistantRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
):
    try:
        assistant, role = await service.update(
            assistant_id,
            user.id,
            body.name,
            body.description,
            "description" in body.model_fields_set,
            body.status,
        )
        return response(assistant, role.value)
    except (
        AssistantNotFoundError,
        AssistantPermissionError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None


@router.delete("/assistants/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assistant(
    assistant_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[AssistantService, Depends(assistant_service)],
) -> Response:
    try:
        await service.delete(assistant_id, user.id)
    except (
        AssistantNotFoundError,
        AssistantPermissionError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
