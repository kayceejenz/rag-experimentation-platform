from pydantic import BaseModel, Field


class CreatePromptRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    purpose: str | None = Field(None, max_length=500)
    description: str | None = Field(None, max_length=2000)
    prompt_type: str
    template: str = Field(min_length=1, max_length=50000)
    change_note: str | None = Field(None, max_length=500)


class CreateVersionRequest(BaseModel):
    template: str = Field(min_length=1, max_length=50000)
    change_note: str | None = Field(None, max_length=500)
