import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from api.dependencies import chat_service, current_user
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.chats.dtos.chat_dto import (
    ChatListResponse,
    ChatResponse,
    CitationResponse,
    CreateChatRequest,
    MessageListResponse,
    MessageResponse,
    SendMessageRequest,
    UpdateChatRequest,
)
from modules.chats.models.chat_model import Chat
from modules.chats.models.error_model import (
    ChatGenerationError,
    ChatNotFoundError,
    ChatPermissionError,
)
from modules.chats.models.message_model import Message
from modules.chats.services.chat_service import ChatService
from modules.projects.models.project_model import (
    ProjectNotFoundError,
    ProjectPermissionError,
)
from modules.knowledge_bots.models import KnowledgeBotNotFoundError

router = APIRouter(tags=["conversations"])
logger = logging.getLogger(__name__)


def message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
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
        assistant_id=chat.assistant_id,
        project_id=chat.project_id,
        created_by=chat.created_by,
        title=chat.title,
        status=chat.status,
        role=role,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


def translate(error: Exception) -> HTTPException:
    if isinstance(
        error, (ChatNotFoundError, KnowledgeBotNotFoundError, ProjectNotFoundError)
    ):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Chat or project not found")
    return HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient project permissions")


@router.post(
    "/assistants/{assistant_id}/conversations",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    assistant_id: UUID,
    body: CreateChatRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chat, role = await service.create_for_assistant(assistant_id, user.id, body.title)
        return response(chat, role.value)
    except (KnowledgeBotNotFoundError, ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.get(
    "/assistants/{assistant_id}/conversations", response_model=ChatListResponse
)
async def list_conversations(
    assistant_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chats, role = await service.list_for_assistant(assistant_id, user.id)
        return ChatListResponse(conversations=[response(chat, role.value) for chat in chats])
    except (KnowledgeBotNotFoundError, ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.get("/conversations/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chat, role = await service.get(chat_id, user.id)
        return response(chat, role.value)
    except (ChatNotFoundError, ProjectNotFoundError, ProjectPermissionError) as error:
        raise translate(error) from None


@router.patch("/conversations/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: UUID,
    body: UpdateChatRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        chat, role = await service.update(chat_id, user.id, body.title, body.status)
        return response(chat, role.value)
    except (ChatNotFoundError, ProjectNotFoundError, ChatPermissionError) as error:
        raise translate(error) from None


@router.delete("/conversations/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
) -> Response:
    try:
        await service.delete(chat_id, user.id)
    except (ChatNotFoundError, ProjectNotFoundError, ChatPermissionError) as error:
        raise translate(error) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/conversations/{chat_id}/messages", response_model=MessageListResponse)
async def list_messages(
    chat_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        messages = await service.list_messages(chat_id, user.id)
        return MessageListResponse(messages=[message_response(item) for item in messages])
    except (ChatNotFoundError, ProjectNotFoundError) as error:
        raise translate(error) from None


@router.post(
    "/conversations/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    chat_id: UUID,
    body: SendMessageRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        message = await service.send_message(chat_id, user.id, body.content)
        return message_response(message)
    except (ChatNotFoundError, ProjectNotFoundError, ChatPermissionError, ProjectPermissionError) as error:
        raise translate(error) from None
    except ChatGenerationError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            {
                "code": "chat_provider_unavailable",
                "message": "The chat model is temporarily unavailable; please try again",
            },
        ) from None


@router.post("/conversations/{chat_id}/messages/stream")
async def stream_message(
    chat_id: UUID,
    body: SendMessageRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[ChatService, Depends(chat_service)],
):
    try:
        await service.get(chat_id, user.id)
    except (ChatNotFoundError, ProjectNotFoundError, ChatPermissionError, ProjectPermissionError) as error:
        raise translate(error) from None

    async def events():
        try:
            async for event in service.stream_message(chat_id, user.id, body.content):
                if event["type"] == "done":
                    event["message"] = message_response(event["message"]).model_dump(mode="json")
                yield f"data: {json.dumps(event)}\n\n"
        except ChatGenerationError:
            logger.exception("Streaming chat generation failed")
            yield f'data: {json.dumps({"type": "error", "message": "The chat model is temporarily unavailable; please try again"})}\n\n'
        except Exception:
            logger.exception("Unexpected error during SSE stream execution")
            yield f'data: {json.dumps({"type": "error", "message": "An unexpected error occurred while streaming"})}\n\n'

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
