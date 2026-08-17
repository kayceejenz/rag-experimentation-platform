from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import current_user, knowledge_base_service
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.knowledge_bases.dtos.knowledge_base_dto import KnowledgeBaseResponse
from modules.knowledge_bases.models.knowledge_base_model import KnowledgeBaseNotFoundError
from modules.knowledge_bases.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(tags=["knowledge bases"])


@router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    knowledge_base_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[KnowledgeBaseService, Depends(knowledge_base_service)],
) -> KnowledgeBaseResponse:
    try:
        return KnowledgeBaseResponse.model_validate(
            service.get(knowledge_base_id, user.id), from_attributes=True
        )
    except KnowledgeBaseNotFoundError:
        raise HTTPException(404, "Knowledge base not found") from None
