from uuid import UUID

from pydantic import BaseModel, Field


class CreateExperimentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(None, max_length=2000)
    hypothesis: str = Field(min_length=1, max_length=5000)
    benchmark_dataset_id: UUID
    metrics: list[str] = Field(min_length=1, max_length=20)
    primary_metric: str
