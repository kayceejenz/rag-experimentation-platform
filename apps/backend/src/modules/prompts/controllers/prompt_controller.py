from typing import Annotated
from uuid import UUID

from api.dependencies import current_user, prompt_service
from fastapi import APIRouter, Depends, HTTPException, Response, status
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.prompts.contracts.prompt_contract import (
    CreatePromptRequest,
    CreateVersionRequest,
)

router = APIRouter(prefix="/projects/{project_id}/prompts", tags=["prompts"])


def translate(error):
    if isinstance(error, PermissionError):
        return HTTPException(403, "You do not have permission to access prompts")
    if isinstance(error, LookupError):
        return HTTPException(404, "Prompt not found")
    return HTTPException(400, str(error))


@router.get("")
def list_prompts(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(prompt_service),
):
    try:
        return {"prompts": service.list(project_id, user.id)}
    except PermissionError as e:
        raise translate(e) from None


@router.post("", status_code=201)
def create_prompt(
    project_id: UUID,
    body: CreatePromptRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(prompt_service),
):
    try:
        prompt, version = service.create(
            project_id,
            user.id,
            body.name,
            body.purpose,
            body.description,
            body.prompt_type,
            body.template,
            body.change_note,
        )
        return {"prompt": prompt, "version": version}
    except (PermissionError, ValueError) as e:
        raise translate(e) from None


@router.get("/{prompt_id}")
def prompt_detail(
    project_id: UUID,
    prompt_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(prompt_service),
):
    try:
        return service.detail(project_id, user.id, prompt_id)
    except (PermissionError, LookupError) as e:
        raise translate(e) from None


@router.post("/{prompt_id}/versions", status_code=201)
def add_version(
    project_id: UUID,
    prompt_id: UUID,
    body: CreateVersionRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(prompt_service),
):
    try:
        return service.add_version(
            project_id, user.id, prompt_id, body.template, body.change_note
        )
    except (PermissionError, LookupError, ValueError) as e:
        raise translate(e) from None


@router.delete("/{prompt_id}", status_code=204)
def archive_prompt(
    project_id: UUID,
    prompt_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(prompt_service),
):
    try:
        service.archive(project_id, user.id, prompt_id)
    except (PermissionError, LookupError) as e:
        raise translate(e) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
