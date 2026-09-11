from typing import Annotated
from uuid import UUID, uuid4

from api.dependencies import benchmark_service, current_user
from fastapi import APIRouter, Depends, HTTPException
from modules.auth.models.auth_user_model import AuthenticatedUser
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/projects/{project_id}/benchmarks", tags=["benchmarks"])
benchmark_service_dependency = Depends(benchmark_service)


class BenchmarkCaseRequest(BaseModel):
    case_id: UUID = Field(default_factory=uuid4)
    question: str = Field(min_length=1, max_length=10000)
    reference_answer: str | None = Field(None, max_length=20000)
    expected_context: str | None = Field(None, max_length=50000)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value):
        if not value.strip():
            raise ValueError("Question cannot be empty")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, values):
        cleaned = sorted({value.strip().lower() for value in values if value.strip()})
        if any(len(value) > 60 for value in cleaned):
            raise ValueError("Tags cannot exceed 60 characters")
        return cleaned


class CreateBenchmarkRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(None, max_length=2000)
    cases: list[BenchmarkCaseRequest] = Field(min_length=1, max_length=1000)


class CreateBenchmarkVersionRequest(BaseModel):
    description: str | None = Field(None, max_length=2000)
    cases: list[BenchmarkCaseRequest] = Field(min_length=1, max_length=1000)


def translate(error):
    if isinstance(error, PermissionError):
        return HTTPException(403, "You do not have permission to access benchmarks")
    if isinstance(error, LookupError):
        return HTTPException(404, "Benchmark dataset not found")
    return HTTPException(400, str(error))


@router.get("")
def list_benchmarks(
    project_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=benchmark_service_dependency,
):
    try:
        return {"datasets": service.list(project_id, user.id)}
    except PermissionError as error:
        raise translate(error) from None


@router.post("", status_code=201)
def create_benchmark(
    project_id: UUID,
    body: CreateBenchmarkRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=benchmark_service_dependency,
):
    try:
        return service.create(
            project_id,
            user.id,
            body.name,
            body.description,
            [case.model_dump(mode="json") for case in body.cases],
        )
    except (PermissionError, ValueError) as error:
        raise translate(error) from None


@router.get("/{dataset_id}")
def benchmark_detail(
    project_id: UUID,
    dataset_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=benchmark_service_dependency,
):
    try:
        return service.detail(project_id, user.id, dataset_id)
    except (PermissionError, LookupError) as error:
        raise translate(error) from None


@router.post("/{dataset_id}/versions", status_code=201)
def create_benchmark_version(
    project_id: UUID,
    dataset_id: UUID,
    body: CreateBenchmarkVersionRequest,
    user: Annotated[AuthenticatedUser, Depends(current_user)],
    service=benchmark_service_dependency,
):
    try:
        return service.add_version(
            project_id,
            user.id,
            dataset_id,
            body.description,
            [case.model_dump(mode="json") for case in body.cases],
        )
    except (PermissionError, LookupError, ValueError) as error:
        raise translate(error) from None
