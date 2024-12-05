from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime

# Modello per "metadata" dentro "procedural"
class Metadata(BaseModel):
    source: str
    type: str
    trigger_type: str
    when: int  # Timestamp (può essere un int o float a seconda delle necessità)

# Modello per un elemento "procedural"
class ProceduralElement(BaseModel):
    id: str
    metadata: Metadata
    page_content: str
    type: str
    score: float

# Modello per "memory" dentro "why"
class Memory(BaseModel):
    episodic: List[str] = []
    declarative: List[str] = []
    procedural: List[ProceduralElement] = []

# Modello per "why"
class Why(BaseModel):
    input: str
    intermediate_steps: List[str] = []
    memory: Memory

# Modello per "model_interactions"
class ModelInteraction(BaseModel):
    model_type: str
    source: str
    prompt: str
    input_tokens: int
    started_at: int  # Timestamp
    reply: List[str]  # Risposta del modello
    output_tokens: int
    ended_at: int  # Timestamp

# Modello per "agent_output"
class AgentOutput(BaseModel):
    output: str
    intermediate_steps: List[str] = []
    return_direct: bool


# Modelli principali
class ChatContent(BaseModel):
    content: str
    user_id: str
    type: Literal["chat"]
    why: Why
    model_interactions: List[ModelInteraction] = []
    agent_output: AgentOutput

class ChatToken(BaseModel):
    type: Literal["chat_token"]
    content: str
