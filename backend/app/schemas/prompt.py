from datetime import datetime

from pydantic import BaseModel, Field


class PromptVersionCreate(BaseModel):
    prompt_id: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    version: str = Field(min_length=1, max_length=40)
    template: str = Field(min_length=1)


class PromptVersionUpdate(BaseModel):
    name: str | None = None
    template: str | None = None


class PromptVersionRead(BaseModel):
    id: str
    prompt_id: str
    name: str
    version: str
    template: str
    created_at: datetime

    model_config = {"from_attributes": True}
