from typing import Dict
from pydantic import BaseModel, Field, field_validator

from cat.db.models import generate_uuid, generate_timestamp


class LLMModel(BaseModel):
    name: str = Field(default_factory=generate_uuid, description="This is the LLM name")
    llm_class: str
    config: Dict = Field(default_factory=dict)
    updated_at: int = Field(default_factory=generate_timestamp)
    
    @field_validator('name', mode='before')
    def handle_none(cls, v):
        """Prevent name is None"""
        return v if v is not None else generate_uuid()