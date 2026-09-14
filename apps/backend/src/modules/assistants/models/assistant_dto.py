from datetime import datetime
from uuid import UUID

from modules.assistants.models.assistant_model import AssistantStatus
from pydantic import BaseModel, ConfigDict, Field


class CreateAssistantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    experiment_variant_run_id: UUID


class UpdateAssistantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    status: AssistantStatus | None = None


class AssistantResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by: UUID
    name: str
    description: str | None
    status: AssistantStatus
    role: str
    created_at: datetime
    updated_at: datetime
    active_revision_version: int | None
    source_run_id: UUID | None
    source_variant_run_id: UUID | None
    source_experiment_name: str | None
    source_variant_name: str | None


class AssistantCandidateResponse(BaseModel):
    variant_run_id: UUID
    run_id: UUID
    experiment_id: UUID
    experiment_name: str
    variant_id: UUID
    variant_name: str
    completed_at: datetime
    aggregate_metrics: dict[str, float]


class AssistantListResponse(BaseModel):
    assistants: list[AssistantResponse]


class AssistantCandidateListResponse(BaseModel):
    candidates: list[AssistantCandidateResponse]


class AssistantLineageResponse(BaseModel):
    assistant: dict
    revision: dict
    experiment: dict
    run: dict
    variant: dict
    index: dict
    system_prompt: dict
    rag_prompt: dict
