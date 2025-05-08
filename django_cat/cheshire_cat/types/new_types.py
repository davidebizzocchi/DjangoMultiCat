# New types that not exist in core, create for multicat plugin

from datetime import datetime
from typing import List, Literal, Optional, Union

from openai import BaseModel
from pydantic import ConfigDict, computed_field, field_validator
from cheshire_cat.types.cat_types import ConversationMessage, MessageWhy, Role
from cheshire_cat.types.mixins import ChatIDMixin

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

class ChatToken(BaseModel, ChatIDMixin):
    type: Literal["chat_token"] = "chat_token"
    text: str

class CatMessage(ConversationMessage, ChatIDMixin):
    """
    Represents a Cat message.

    Attributes
    ----------
    type : str
        The type of message. Defaults to "chat".
    user_id : str
        Unique identifier for the user associated with the message.
    when : float
        The timestamp when the message was sent. Defaults to the current time.
    who : str
        The name of the message author.
    text : Optional[str], default=None
        The text content of the message.
    image : Optional[str], default=None
        Image file URLs or base64 data URIs that represent image associated with the message.
    audio : Optional[str], default=None
        Audio file URLs or base64 data URIs that represent audio associated with the message.
    why : Optional[MessageWhy]
        Additional contextual information related to the message.

    Notes
    -----
    - The `content` parameter and attribute are deprecated. Use `text` instead.
    """

    who: str = "AI"
    type: str = "chat" # For now is always "chat" and is not used
    why: Optional[MessageWhy] = None

    def __init__(
        self,
        user_id: str,
        who: str = "AI",
        text: Optional[str] = None,
        image: Optional[str] = None,
        audio: Optional[str] = None,
        why: Optional[MessageWhy] = None,
        **kwargs,
    ):
        if "content" in kwargs:
            print("The `content` parameter is deprecated. Use `text` instead.")    
            text = kwargs.pop("content")  # Map 'content' to 'text'

        super().__init__(user_id=user_id, text=text, image=image, audio=audio, why=why, who=who, **kwargs)

    @computed_field
    @property
    def content(self) -> str:
        """
        This attribute is deprecated. Use `text` instead.

        The text content of the message. Use `text` instead.

        Returns
        -------
        str
            The text content of the message.
        """
        return self.text
    
    @content.setter
    def content(self, value):
        print("The `content` attribute is deprecated. Use `text` instead.")
        self.text = value

    @property
    def role(self) -> Role:
        """The role of the message author."""
        return Role.AI