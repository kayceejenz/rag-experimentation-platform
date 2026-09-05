from uuid import UUID

from modules.experiments.contracts.generation_configuration import (
    GenerationConfiguration,
)
from modules.experiments.contracts.retrieval_configuration import RetrievalConfiguration
from pydantic import BaseModel, Field


class CreateVariantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    index_specification_id: UUID
    system_prompt_version_id: UUID
    rag_prompt_version_id: UUID
    retrieval: RetrievalConfiguration = Field(default_factory=RetrievalConfiguration)
    generation: GenerationConfiguration = Field(default_factory=GenerationConfiguration)
