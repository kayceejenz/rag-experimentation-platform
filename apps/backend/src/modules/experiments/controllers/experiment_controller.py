from typing import Annotated
from uuid import UUID

from api.dependencies import current_user, experiment_service
from fastapi import APIRouter, Depends, HTTPException
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.experiments.contracts.create_experiment_request import (
    CreateExperimentRequest,
)
from modules.experiments.contracts.create_variation import CreateVariantRequest
from modules.experiments.contracts.start_experiment_run import (
    StartExperimentRunRequest,
)

router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["experiments"])


def translate(error):
    if isinstance(error, PermissionError):
        return HTTPException(403, "You do not have permission to access experiments")
    if isinstance(error, LookupError):
        return HTTPException(404, str(error))
    if isinstance(error, RuntimeError):
        return HTTPException(409, str(error))
    return HTTPException(400, str(error))


@router.get("")
def catalog(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.catalog(project_id, user.id)
    except PermissionError as error:
        raise translate(error) from None


@router.post("", status_code=201)
def create_experiment(
    project_id: UUID,
    body: CreateExperimentRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.create(
            project_id,
            user.id,
            body.name,
            body.description,
            body.hypothesis,
            body.benchmark_dataset_id,
            body.metrics,
            body.primary_metric,
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise translate(error) from None


@router.get("/runs")
def project_runs(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.project_runs(project_id, user.id)
    except PermissionError as error:
        raise translate(error) from None


@router.get("/{experiment_id}")
def detail(
    project_id: UUID,
    experiment_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.detail(project_id, user.id, experiment_id)
    except (PermissionError, LookupError) as error:
        raise translate(error) from None


@router.post("/{experiment_id}/variants", status_code=201)
def create_variant(
    project_id: UUID,
    experiment_id: UUID,
    body: CreateVariantRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.add_variant(
            project_id,
            user.id,
            experiment_id,
            body.name,
            body.index_specification_id,
            body.system_prompt_version_id,
            body.rag_prompt_version_id,
            body.retrieval.model_dump(),
            body.generation.model_dump(),
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise translate(error) from None


@router.delete("/{experiment_id}/variants/{variant_id}", status_code=204)
def delete_variant(
    project_id: UUID,
    experiment_id: UUID,
    variant_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        service.delete_variant(project_id, user.id, experiment_id, variant_id)
    except (PermissionError, LookupError, RuntimeError) as error:
        raise translate(error) from None


@router.post("/{experiment_id}/runs", status_code=202)
def start_run(
    project_id: UUID,
    experiment_id: UUID,
    body: StartExperimentRunRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.start_run(
            project_id, user.id, experiment_id, body.variant_ids
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise translate(error) from None


@router.get("/{experiment_id}/runs/{run_id}")
def run_detail(
    project_id: UUID,
    experiment_id: UUID,
    run_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=Depends(experiment_service),
):
    try:
        return service.run_detail(project_id, user.id, experiment_id, run_id)
    except (PermissionError, LookupError) as error:
        raise translate(error) from None
