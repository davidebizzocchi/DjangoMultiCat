from typing import List, Union
from typing_extensions import Annotated
from pydantic import BaseModel, BeforeValidator, Field

from cat.mad_hatter.decorators import plugin

def split_string(v: Union[str, List[str]]) -> List[str]:
    """Convert comma-separated string to list if needed"""
    
    if v is None:
        return []
    
    if isinstance(v, str):
        if not v.strip():  # Empty string
            return []
        return [x.strip() for x in v.split(',') if x.strip()]
    
    if isinstance(v, list):
        return v
    
    raise ValueError("limited_plugins must be a list")

class MultiCatSettings(BaseModel):
    max_users: int = Field(
        title="[CACHE] Maximum number of users",
        default=100
    )
    users_timeout: int = Field(
        title="[CACHE] Timeout for users (in seconds)",
        default=3600
    )
    max_chat_sessions: int = Field(
        title="[CACHE] Maximum number of chat for each user",
        default=100
    )
    chat_session_timeout: int = Field(
        title="[CACHE] Timeout for chat session (in seconds)",
        default=3600
    )
    limited_plugins: Annotated[List[str], BeforeValidator(split_string)] = Field(
        title="[LIMITED PLUGINS] List of plugins to limit. (string comma separated)",
        default=[]
    )

@plugin
def settings_model() -> MultiCatSettings:
    """
    Load the settings for the plugin
    """
    return MultiCatSettings