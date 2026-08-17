from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import current_user, job_service
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.jobs.dtos.job_dto import IngestionJobResponse
from modules.jobs.services.job_service import JobNotFoundError, JobService

router = APIRouter(prefix="/ingestion-jobs", tags=["ingestion jobs"])


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_job(
    job_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service: Annotated[JobService, Depends(job_service)],
) -> IngestionJobResponse:
    try:
        return IngestionJobResponse.model_validate(
            service.get(job_id, user.id), from_attributes=True
        )
    except JobNotFoundError:
        raise HTTPException(404, "Ingestion job not found") from None
