from pydantic import BaseModel, Field


class GenerationConfiguration(BaseModel):
    model: str = Field(min_length=1, max_length=160)
    temperature: float = Field(default=0, ge=0, le=2)
    max_output_tokens: int = Field(default=2048, ge=64, le=65536)
