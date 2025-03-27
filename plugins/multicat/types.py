from typing import Dict, List
from pydantic import BaseModel, Field

class Agent(BaseModel):
    id: str = "default"
    name: str = ""
    instructions: str = ""
    metadata: Dict = Field(default_factory=dict)  # This for safe mutable default values