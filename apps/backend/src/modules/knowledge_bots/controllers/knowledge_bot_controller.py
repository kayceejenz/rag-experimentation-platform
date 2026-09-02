from typing import Annotated
from uuid import UUID

from api.dependencies import current_user, knowledge_bot_service
from fastapi import APIRouter, Depends, HTTPException, Response, status
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.knowledge_bots.models.dtos import (
    CreateKnowledgeBotRequest,
    KnowledgeBotListResponse,
    KnowledgeBotResponse,
    UpdateKnowledgeBotRequest,
)
from modules.knowledge_bots.models.models import (
    KnowledgeBot,
    KnowledgeBotNotFoundError,
    KnowledgeBotPermissionError,
)
from modules.knowledge_bots.services.knowledge_bot_service import KnowledgeBotService
from modules.projects.models.project_model import (
    ProjectNotFoundError,
    ProjectPermissionError,
)

router = APIRouter(tags=["assistants"])


def response(bot: KnowledgeBot, role: str) -> KnowledgeBotResponse:
    return KnowledgeBotResponse(
        id=bot.id,
        project_id=bot.project_id,
        created_by=bot.created_by,
        name=bot.name,
        description=bot.description,
        status=bot.status,
        role=role,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


def translate(error: Exception) -> HTTPException:
    if isinstance(error, (KnowledgeBotNotFoundError, ProjectNotFoundError)):
        return HTTPException(
            status.HTTP_404_NOT_FOUND, "Assistant or project not found"
        )
    return HTTPException(
        status.HTTP_403_FORBIDDEN, "Insufficient assistant permissions"
    )


@router.post(
    "/projects/{project_id}/assistants",
    response_model=KnowledgeBotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bot(
    project_id: UUID,
    body: CreateKnowledgeBotRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[KnowledgeBotService, Depends(knowledge_bot_service)],
):
    try:
        bot, role = await service.create(
            project_id, user.id, body.name, body.description
        )
        return response(bot, role.value)
    except (
        ProjectNotFoundError,
        ProjectPermissionError,
        KnowledgeBotPermissionError,
    ) as error:
        raise translate(error) from None


@router.get(
    "/projects/{project_id}/assistants", response_model=KnowledgeBotListResponse
)
async def list_bots(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[KnowledgeBotService, Depends(knowledge_bot_service)],
):
    try:
        bots, role = await service.list(project_id, user.id)
        return KnowledgeBotListResponse(
            assistants=[response(bot, role.value) for bot in bots]
        )
    except (ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.get("/assistants/{bot_id}", response_model=KnowledgeBotResponse)
async def get_bot(
    bot_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[KnowledgeBotService, Depends(knowledge_bot_service)],
):
    try:
        bot, role = await service.get(bot_id, user.id)
        return response(bot, role.value)
    except (
        KnowledgeBotNotFoundError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None


@router.patch("/assistants/{bot_id}", response_model=KnowledgeBotResponse)
async def update_bot(
    bot_id: UUID,
    body: UpdateKnowledgeBotRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[KnowledgeBotService, Depends(knowledge_bot_service)],
):
    try:
        bot, role = await service.update(
            bot_id,
            user.id,
            body.name,
            body.description,
            "description" in body.model_fields_set,
            body.status,
        )
        return response(bot, role.value)
    except (
        KnowledgeBotNotFoundError,
        KnowledgeBotPermissionError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None


@router.delete("/assistants/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[KnowledgeBotService, Depends(knowledge_bot_service)],
) -> Response:
    try:
        await service.delete(bot_id, user.id)
    except (
        KnowledgeBotNotFoundError,
        KnowledgeBotPermissionError,
        ProjectNotFoundError,
        ProjectPermissionError,
    ) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
