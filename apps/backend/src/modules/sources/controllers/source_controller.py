from typing import Annotated
from uuid import UUID

from api.dependencies import current_user, settings, source_service
from core.settings import Settings
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from integrations.storage import cleanup_temp
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.sources.dtos.source_dto import (
    CreateKnowledgeFolderRequest,
    KnowledgeActivityListResponse,
    KnowledgeActivityResponse,
    KnowledgeFolderListResponse,
    KnowledgeFolderResponse,
    SourceInspectionResponse,
    SourceListResponse,
    SourceResponse,
)
from modules.sources.models.error_model import (
    SourceNotFoundError,
    SourcePermissionError,
    SourceTooLargeError,
)
from modules.sources.services.source_service import SourceService
from pydantic import BaseModel
from starlette.background import BackgroundTask

router = APIRouter(tags=["knowledge-base sources"])


class PipelineTriggerResponse(BaseModel):
    stage: str
    queued: int


class PipelinePresetResponse(BaseModel):
    chunking_strategy: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int


@router.get(
    "/knowledge-bases/{knowledge_base_id}/pipeline",
    response_model=PipelinePresetResponse,
)
def pipeline_preset(
    knowledge_base_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
    config: Annotated[Settings, Depends(settings)],
) -> PipelinePresetResponse:
    try:
        service.list(knowledge_base_id, user.id)
    except SourceNotFoundError:
        raise HTTPException(404, "Source not found") from None
    return PipelinePresetResponse(
        chunking_strategy="element",
        embedding_provider=config.embedding_provider,
        embedding_model=config.embedding_model,
        embedding_dimensions=config.embedding_dimensions,
    )


@router.post(
    "/knowledge-bases/{knowledge_base_id}/pipeline/{stage}",
    response_model=PipelineTriggerResponse,
)
def trigger_pipeline_stage(
    knowledge_base_id: UUID,
    stage: str,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> PipelineTriggerResponse:
    if stage not in {"chunk", "index"}:
        raise HTTPException(400, "Stage must be chunk or index")
    try:
        return PipelineTriggerResponse(
            stage=stage,
            queued=service.trigger(knowledge_base_id, user.id, stage),
        )
    except SourcePermissionError:
        raise HTTPException(403, "Insufficient Source permissions") from None


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
    folder_id: Annotated[UUID | None, Form()] = None,
) -> SourceResponse:
    try:
        return response(service.upload(knowledge_base_id, user.id, file, folder_id))
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
            sources=[
                response(item) for item in service.list(knowledge_base_id, user.id)
            ]
        )
    except SourceNotFoundError:
        raise HTTPException(404, "Knowledge base not found") from None


@router.get(
    "/knowledge-bases/{knowledge_base_id}/activity",
    response_model=KnowledgeActivityListResponse,
)
def knowledge_activity(
    knowledge_base_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
) -> KnowledgeActivityListResponse:
    try:
        return KnowledgeActivityListResponse(
            events=[
                KnowledgeActivityResponse(**event)
                for event in service.activity(knowledge_base_id, user.id)
            ]
        )
    except SourceNotFoundError:
        raise HTTPException(404, "Knowledge base not found") from None


@router.get(
    "/knowledge-bases/{knowledge_base_id}/folders",
    response_model=KnowledgeFolderListResponse,
)
def list_folders(
    knowledge_base_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
):
    try:
        return KnowledgeFolderListResponse(
            folders=[
                KnowledgeFolderResponse(**folder)
                for folder in service.folders(knowledge_base_id, user.id)
            ]
        )
    except SourceNotFoundError:
        raise HTTPException(404, "Knowledge base not found") from None


@router.post(
    "/knowledge-bases/{knowledge_base_id}/folders",
    response_model=KnowledgeFolderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_folder(
    knowledge_base_id: UUID,
    body: CreateKnowledgeFolderRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[SourceService, Depends(source_service)],
):
    try:
        return KnowledgeFolderResponse(
            **service.create_folder(
                knowledge_base_id, user.id, body.name, body.parent_id
            )
        )
    except SourcePermissionError:
        raise HTTPException(403, "Insufficient knowledge-base permissions") from None


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
        content_disposition_type="inline",
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
