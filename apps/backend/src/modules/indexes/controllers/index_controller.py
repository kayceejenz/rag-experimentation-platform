from typing import Annotated
from uuid import UUID

from api.dependencies import current_user, index_service
from fastapi import APIRouter, Depends, HTTPException, Response, status
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.indexes.contracts.create_index_contract import CreateIndexRequest
from modules.indexes.contracts.refresh_index_contract import RefreshIndexRequest

router = APIRouter(prefix="/projects/{project_id}/indexes", tags=["indexes"])
index_dependency = Depends(index_service)


@router.get("")
def list_indexes(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=index_dependency,
):
    try:
        models, builds = service.catalog(project_id, user.id)
        return {
            "embedding_models": models,
            "indexes": builds,
            "chunking_strategies": [
                {"id": "by_title", "name": "By title", "provider": "Unstructured"},
                {"id": "basic", "name": "Basic", "provider": "Unstructured"},
            ],
        }
    except PermissionError:
        raise HTTPException(403, "Insufficient project permissions") from None


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_index(
    project_id: UUID,
    body: CreateIndexRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=index_dependency,
):
    try:
        specification, queued, documents = service.create(
            project_id,
            user.id,
            body.knowledge_base_id,
            body.name.strip(),
            body.embedding_model_id,
            body.chunking_strategy,
            body.folder_ids,
        )
        return {
            "specification_id": specification.id,
            "configuration": specification.configuration,
            "queued_jobs": queued,
            "documents": documents,
        }
    except PermissionError:
        raise HTTPException(403, "Insufficient project permissions") from None
    except LookupError:
        raise HTTPException(
            404, "Embedding model or Knowledge Base not found"
        ) from None
    except ValueError as error:
        raise HTTPException(400, str(error)) from None


@router.get("/{specification_id}")
def index_detail(
    project_id: UUID,
    specification_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=index_dependency,
):
    try:
        return service.detail(project_id, user.id, specification_id)
    except PermissionError:
        raise HTTPException(403, "Insufficient project permissions") from None
    except LookupError:
        raise HTTPException(404, "Index not found") from None


@router.post("/{specification_id}/refresh", status_code=status.HTTP_202_ACCEPTED)
def refresh_index(
    project_id: UUID,
    specification_id: UUID,
    body: RefreshIndexRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=index_dependency,
):
    try:
        return service.refresh(
            project_id, user.id, specification_id, body.knowledge_base_id
        )
    except PermissionError:
        raise HTTPException(403, "Insufficient project permissions") from None
    except LookupError:
        raise HTTPException(404, "Index or Knowledge Base not found") from None
    except ValueError as error:
        raise HTTPException(400, str(error)) from None


@router.delete("/{specification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_index(
    project_id: UUID,
    specification_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=index_dependency,
):
    try:
        service.delete(project_id, user.id, specification_id)
    except PermissionError:
        raise HTTPException(403, "Insufficient project permissions") from None
    except LookupError:
        raise HTTPException(404, "Index not found") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{specification_id}/artifacts/{artifact_id}/preview")
def preview_index_artifact(
    project_id: UUID,
    specification_id: UUID,
    artifact_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=index_dependency,
):
    try:
        return service.artifact_preview(
            project_id, user.id, specification_id, artifact_id
        )
    except PermissionError:
        raise HTTPException(403, "Insufficient project permissions") from None
    except LookupError:
        raise HTTPException(404, "Index output not found") from None
