from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.dependencies import current_user, project_service
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.projects.dtos.project_dto import (
    CreateProjectRequest,
    ProjectListResponse,
    ProjectResponse,
    UpdateProjectRequest,
    AddProjectMemberRequest,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    UpdateProjectMemberAccessRequest,
)
from modules.projects.models.project_model import (
    DefaultProjectDeletionError,
    ProjectAccess,
    ProjectNotFoundError,
    ProjectPermissionError,
    ProjectMemberConflictError,
)
from modules.projects.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def response(access: ProjectAccess) -> ProjectResponse:
    p = access.project
    permissions = access.permissions
    if access.role.value == "owner":
        permissions = {feature: {"view": True, "manage": True} for feature in ProjectService.FEATURES}
    return ProjectResponse(
        id=p.id,
        workspace_id=p.workspace_id,
        owner_id=p.owner_id,
        name=p.name,
        description=p.description,
        role=access.role.value,
        is_default=p.is_default,
        created_at=p.created_at,
        updated_at=p.updated_at,
        permissions=permissions,
    )


def translate(error: Exception) -> HTTPException:
    if isinstance(error, ProjectNotFoundError):
        return HTTPException(404, "Project not found")
    if isinstance(error, DefaultProjectDeletionError):
        return HTTPException(409, "The default project cannot be deleted")
    if isinstance(error, ProjectMemberConflictError):
        return HTTPException(409, "This account is already a project member")
    return HTTPException(403, "Insufficient project permissions")


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ProjectService, Depends(project_service)],
):
    return response(await service.create(user.id, body.name, body.description))


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ProjectService, Depends(project_service)],
):
    return ProjectListResponse(projects=[response(item) for item in await service.list(user.id)])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ProjectService, Depends(project_service)],
):
    try:
        return response(await service.get(project_id, user.id))
    except ProjectNotFoundError as error:
        raise translate(error) from None


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    body: UpdateProjectRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ProjectService, Depends(project_service)],
):
    try:
        return response(
            await service.update(
                project_id,
                user.id,
                body.name,
                body.description,
                "description" in body.model_fields_set,
            )
        )
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ProjectService, Depends(project_service)],
) -> Response:
    try:
        await service.delete(project_id, user.id)
    except (ProjectNotFoundError, ProjectPermissionError, DefaultProjectDeletionError) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def member_response(member) -> ProjectMemberResponse:
    permissions = member["permissions"]
    if member["role"] == "owner":
        permissions = {feature: {"view": True, "manage": True} for feature in ProjectService.FEATURES}
    return ProjectMemberResponse(**{**member, "permissions": permissions})


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_project_members(project_id: UUID, user: Annotated[AuthenticatedUser, Depends(current_user)], service: Annotated[ProjectService, Depends(project_service)]):
    try:
        return ProjectMemberListResponse(members=[member_response(item) for item in await service.members(project_id, user.id)])
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.post("/{project_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_project_member(project_id: UUID, body: AddProjectMemberRequest, user: Annotated[AuthenticatedUser, Depends(current_user)], service: Annotated[ProjectService, Depends(project_service)]):
    try:
        await service.add_member(project_id, user.id, body.email, body.permissions)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    except (ProjectNotFoundError, ProjectPermissionError, ProjectMemberConflictError) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_project_member(project_id: UUID, member_id: UUID, body: UpdateProjectMemberAccessRequest, user: Annotated[AuthenticatedUser, Depends(current_user)], service: Annotated[ProjectService, Depends(project_service)]):
    try:
        await service.update_member_access(project_id, user.id, member_id, body.permissions)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(project_id: UUID, member_id: UUID, user: Annotated[AuthenticatedUser, Depends(current_user)], service: Annotated[ProjectService, Depends(project_service)]):
    try:
        await service.remove_member(project_id, user.id, member_id)
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
