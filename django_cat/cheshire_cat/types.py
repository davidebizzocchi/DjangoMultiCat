from pydantic import BaseModel, field_validator
from typing import List, Literal, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import time
import traceback
from enum import Enum

# Modello copiato da cat.utils
class BaseModelDict(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        arbitrary_types_allowed=True,
        protected_namespaces=() # avoid warning for `model_xxx` attributes
    )

    def __getitem__(self, key):
        # deprecate dictionary usage
        stack = traceback.extract_stack(limit=2)
        line_code = traceback.format_list(stack)[0].split("\n")[1].strip()

        # return attribute
        return getattr(self, key)

    def __setitem__(self, key, value):
        # deprecate dictionary usage
        stack = traceback.extract_stack(limit=2)
        line_code = traceback.format_list(stack)[0].split("\n")[1].strip()

        # set attribute
        setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __delitem__(self, key):
        delattr(self, key)

    def _get_all_attributes(self):
        # return {**self.model_fields, **self.__pydantic_extra__}
        return self.model_dump()

    def keys(self):
        return self._get_all_attributes().keys()

    def values(self):
        return self._get_all_attributes().values()

    def items(self):
        return self._get_all_attributes().items()

    def __contains__(self, key):
        return key in self.keys()


# Modelli copiati da cat.convo.messages #

class ModelInteraction(BaseModel):
    model_type: Literal["llm", "embedder"]
    source: str
    prompt: str
    input_tokens: int
    started_at: float = Field(default_factory=lambda: time.time())

    model_config = ConfigDict(
        protected_namespaces=()
    )


class LLMModelInteraction(ModelInteraction):
    model_type: Literal["llm"] = Field(default="llm")
    reply: str
    output_tokens: int
    ended_at: float


class EmbedderModelInteraction(ModelInteraction):
    model_type: Literal["embedder"] = Field(default="embedder")
    source: str = Field(default="recall")
    reply: List[float]


class MessageWhy(BaseModelDict):
    """Class for wrapping message why

    Variables:
        input (str): input message
        intermediate_steps (List): intermediate steps
        memory (dict): memory
        model_interactions (List[LLMModelInteraction | EmbedderModelInteraction]): model interactions
    """

    input: str
    intermediate_steps: List
    memory: dict
    model_interactions: List[LLMModelInteraction | EmbedderModelInteraction]


class ChatContent(BaseModelDict):
    """Class for wrapping cat message

    Variables:
        content (str): cat message
        user_id (str): user id
    """

    content: str
    user_id: str
    type: str = "chat"
    why: MessageWhy | None = None
    chat_id: Optional[str] = "default"

class ChatToken(BaseModel):
    type: Literal["chat_token"] = "chat_token"
    content: str
    chat_id: Optional[str] = "default"

class Role(str, Enum):
    AI = "AI"
    Human = "Human"

class ChatHistoryMessage(BaseModel):
    who: str
    message: str
    why: Union[MessageWhy, dict] = {}  # Modificato per accettare anche dict vuoto
    when: datetime
    role: Role

    model_config = ConfigDict(
        use_enum_values=True
    )

    @field_validator('when', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v
    
    @field_validator('why', mode='before') 
    @classmethod
    def validate_why(cls, v):
        if isinstance(v, dict) and not v:  # Se è un dict vuoto
            return v
        if isinstance(v, dict):  # Se è un dict non vuoto
            return MessageWhy(**v)
        return v

class ChatHistory(BaseModel):
    messages: List[ChatHistoryMessage] = []

class GenericMessage(BaseModel):
    type: str
    content: Union[str, dict, None] = None

    model_config = ConfigDict(
        extra="allow",
        protected_namespaces=()
    )

class Notification(BaseModel):
    type: str = "notification"
    content: str
    received_at: float = Field(default_factory=lambda: time.time())

    @property
    def message(self):
        return self.content

class DocReadingProgress(BaseModel):
    type: Literal["doc-reading-progress"]
    status: Literal["done", "progress"]
    perc_read: int 
    source: str
    received_at: float = Field(default_factory=lambda: time.time())