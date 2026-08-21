from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from api.dependencies import current_user, source_service
from integrations.storage import cleanup_temp
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
            {"code": "file_too_large", "message": "File size must not exceed 10 MB"},
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
    except SourceNotFoundError:
        raise HTTPException(404, "Source not found") from None
    return SourceInspectionResponse(**result)


@router.get(
    "/knowledge-bases/{knowledge_base_id}/sources/{source_id}/file",
)
def download_source_file(
    knowledge_base_id: UUID,
    source_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> FileResponse:
    try:
        path, temporary, content_type, filename = service.load_file(
            knowledge_base_id, source_id, user.id
        )
    except SourceNotFoundError:
        raise HTTPException(404, "Source not found") from None
    background = BackgroundTask(cleanup_temp, path) if temporary else None
    return FileResponse(
        path,
        media_type=content_type,
        filename=filename,
        background=background,
    )


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
