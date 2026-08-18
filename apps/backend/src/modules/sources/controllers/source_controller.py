from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.dependencies import current_user, source_service
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.sources.dtos.source_dto import SourceInspectionResponse, SourceListResponse, SourceResponse
from modules.sources.models.error_model import SourceNotFoundError, SourcePermissionError, SourceTooLargeError
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
    except SourceTooLargeError:
        raise HTTPException(
            413,
            {"code": "file_too_large", "message": "File size must not exceed 5 MB"},
        ) from None


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


@router.get(
    "/knowledge-bases/{knowledge_base_id}/sources/{source_id}/inspection",
    response_model=SourceInspectionResponse,
)
def inspect_source(
    knowledge_base_id: UUID,
    source_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> SourceInspectionResponse:
    try:
        result = service.inspection(knowledge_base_id, source_id, user.id)
        version = result["version"]
        return SourceInspectionResponse(
            source_id=source_id,
            version_id=version["id"],
            version=version["version"],
            filename=version["filename"],
            status=version["status"],
            parser_name=version["parser_name"],
            parser_version=version["parser_version"],
            parser_config=version["parser_config"] or {},
            element_count=version["element_count"],
            chunk_count=version["chunk_count"],
            processing_started_at=version["processing_started_at"],
            processing_completed_at=version["processing_completed_at"],
            error_code=version["error_code"],
            error_message=version["error_message"],
            elements=result["elements"],
            chunks=result["chunks"],
        )
    except SourceNotFoundError:
        raise HTTPException(404, "Source not found") from None


@router.delete(
    "/knowledge-bases/{knowledge_base_id}/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_source(
    knowledge_base_id: UUID,
    source_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> None:
    try:
        service.delete(knowledge_base_id, source_id, user.id)
    except SourceNotFoundError:
        raise HTTPException(404, "Source not found") from None
