from pydantic import BaseModel, Field


class RetrievalConfiguration(BaseModel):
    top_k: int = Field(default=5, ge=1, le=100)
    min_score: float = Field(default=0, ge=0, le=1)
