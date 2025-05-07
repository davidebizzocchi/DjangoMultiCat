#type: ignore
from typing import Dict, Optional
from pydantic import BaseModel, Field

from pydantic import BaseModel, Field, field_validator

from cat.factory.llm import get_llm_from_name

class LLM(BaseModel):
    name: str
    llm_class: str
    config: Dict = Field(default_factory=dict)

    def get_llm_from_config(self):
        """Get LLM from settings"""
        llm = get_llm_from_name(self.name)
        if llm is None:
            raise ValueError(f"LLM {self.name} not found")
        return llm.get_llm_from_config(self.config)
    
    # updated_at: int = Field(default_factory=generate_timestamp)
    
    # @field_validator('name', mode='before')
    # def handle_none(cls, v):
    #     """Prevent name is None"""
    #     return v if v is not None else generate_uuid()

class Agent(BaseModel):
    id: str = "default"
    name: str = ""
    instructions: str = ""
    metadata: Dict = Field(default_factory=dict)  # This for safe mutable default values
    enable_vector_search: bool = Field(default=True)

    llm_name: Optional[str] = None