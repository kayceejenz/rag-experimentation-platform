from typing import Annotated
from uuid import UUID

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from api.dependencies import chat_service, current_user
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.chats.dtos.chat_dto import (
    ChatListResponse,
    ChatResponse,
    CreateChatRequest,
    UpdateChatRequest,
    SendMessageRequest,
    MessageResponse,
    MessageListResponse,
    CitationResponse,
)
from modules.chats.models.chat_model import Chat
from modules.chats.models.message_model import Message
from modules.chats.models.error_model import ChatGenerationError, ChatNotFoundError, ChatPermissionError
from modules.chats.services.chat_service import ChatService
from modules.projects.models.project_model import ProjectNotFoundError, ProjectPermissionError

router = APIRouter(tags=["chats"])
logger = logging.getLogger(__name__)


def message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        role=message.role,
        content=message.content,
        citations=[
            CitationResponse(
                source_id=citation.source_id,
                chunk_id=citation.chunk_id,
                source_filename=citation.source_filename,
                excerpt=citation.excerpt,
                page_number=citation.page_number,
                element_ids=list(citation.element_ids),
            )
            for citation in message.citations
        ],
        created_at=message.created_at,
    )


def response(chat: Chat, role: str) -> ChatResponse:
    return ChatResponse(
        id=chat.id,
        project_id=chat.project_id,
        created_by=chat.created_by,
        knowledge_base_id=chat.knowledge_base_id,
        title=chat.title,
        status=chat.status,
        role=role,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


def translate(error: Exception) -> HTTPException:
    if isinstance(error, ChatNotFoundError | ProjectNotFoundError):
        return HTTPException(404, "Chat or project not found")
    return HTTPException(403, "Insufficient project permissions")


@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat(
    project_id: UUID,
    body: CreateChatRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chat, role = service.create(project_id, user.id, body.title)
        return response(chat, role.value)
    except (ProjectNotFoundError, ProjectPermissionError, ChatPermissionError) as error:
        raise translate(error) from None


@router.get("/projects/{project_id}/chats", response_model=ChatListResponse)
def list_chats(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chats, role = service.list(project_id, user.id)
        return ChatListResponse(chats=[response(chat, role.value) for chat in chats])
    except ProjectNotFoundError as error:
        raise translate(error) from None


@router.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chat, role = service.get(chat_id, user.id)
        return response(chat, role.value)
    except (ChatNotFoundError, ProjectNotFoundError) as error:
        raise translate(error) from None


@router.patch("/chats/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: UUID,
    body: UpdateChatRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chat, role = service.update(chat_id, user.id, body.title, body.status)
        return response(chat, role.value)
    except (ChatNotFoundError, ProjectNotFoundError, ChatPermissionError) as error:
        raise translate(error) from None


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
) -> Response:
    try:
        service.delete(chat_id, user.id)
    except (ChatNotFoundError, ProjectNotFoundError, ChatPermissionError) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
def list_messages(
    chat_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        return MessageListResponse(
            messages=[message_response(item) for item in service.list_messages(chat_id, user.id)]
        )
    except (ChatNotFoundError, ProjectNotFoundError) as error:
        raise translate(error) from None


@router.post(
    "/chats/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    chat_id: UUID,
    body: SendMessageRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        return message_response(service.send_message(chat_id, user.id, body.content))
    except (ChatNotFoundError, ProjectNotFoundError) as error:
        raise translate(error) from None
    except ChatGenerationError:
        raise HTTPException(
            502,
            {
                "code": "chat_provider_unavailable",
                "message": "The chat model is temporarily unavailable; please try again",
            },
        ) from None


@router.post("/chats/{chat_id}/messages/stream")
def stream_message(
    chat_id: UUID,
    body: SendMessageRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    def events():
        try:
            for event in service.stream_message(chat_id, user.id, body.content):
                if event["type"] == "done":
                    event["message"] = message_response(event["message"]).model_dump(mode="json")
                yield f"data: {json.dumps(event)}\n\n"
        except (ChatNotFoundError, ProjectNotFoundError):
            yield f'data: {json.dumps({"type": "error", "message": "Chat not found"})}\n\n'
        except ChatGenerationError as error:
            logger.exception("Streaming chat generation failed", exc_info=error)
            yield f'data: {json.dumps({"type": "error", "message": "The chat model is temporarily unavailable; please try again"})}\n\n'

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
