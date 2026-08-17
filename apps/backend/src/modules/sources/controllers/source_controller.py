from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.dependencies import current_user, source_service
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.sources.dtos.source_dto import SourceListResponse, SourceResponse
from modules.sources.models.error_model import SourceNotFoundError, SourcePermissionError
from modules.sources.services.source_service import SourceService

router = APIRouter(tags=["knowledge-base sources"])


def response(source) -> SourceResponse:
    return SourceResponse.model_validate(source, from_attributes=True)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_source(
    knowledge_base_id: UUID,
    file: Annotated[UploadFile, File()],
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> SourceResponse:
    try:
        return response(service.upload(knowledge_base_id, user.id, file))
    except SourceNotFoundError:
        raise HTTPException(404, "Knowledge base not found") from None
    except SourcePermissionError:
        raise HTTPException(403, "Insufficient knowledge-base permissions") from None


@router.get(
    "/knowledge-bases/{knowledge_base_id}/sources",
    response_model=SourceListResponse,
)
def list_sources(
    knowledge_base_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> SourceListResponse:
    try:
        return SourceListResponse(
            sources=[response(item) for item in service.list(knowledge_base_id, user.id)]
        )
    except SourceNotFoundError:
        raise HTTPException(404, "Knowledge base not found") from None
