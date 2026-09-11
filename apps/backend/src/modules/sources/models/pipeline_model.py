from pydantic import BaseModel


class PipelineTriggerResponse(BaseModel):
    stage: str
    queued: int


class PipelinePresetResponse(BaseModel):
    chunking_strategy: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
