from typing import Any, List, Union

from cat.auth.permissions import AuthUserInfo

from cat.convo.messages import CatMessage
from cat.log import log

from cat.looking_glass.stray_cat import StrayCat
from cat.memory.working_memory import WorkingMemory
from cat.cache.cache_item import CacheItem

from cat.looking_glass.stray_cat import MSG_TYPES

# Common
from cat.plugins.multicat.refactory.stray_cat.common import CommonStrayCat

from cat.plugins.multicat.agents.crud import manager as agent_manager


stray_cat_attr = {k: v for k, v in StrayCat.__dict__.items()}
MyStrayCat: StrayCat = type("MyStrayCat", StrayCat.__bases__, stray_cat_attr)

# A perfect son
class SonStrayCat(MyStrayCat, CommonStrayCat):
    chat_id: str
    
    # str: key, bool: is a class attribute
    cache_keys: List[tuple[str, bool]] = [
        ("user_id", True),
        ("chat_id", True)
    ]

    """
    This is the Very StrayCat

    chat_id: str is the chat_id of the chat
    stray_cat: StrayCat is the stray_cat object (the father)

    *other: args and kwargs are the same as StrayCat
    """
    def __init__(
            self,
            chat_id,
            stray_cat: StrayCat,
            user_data: AuthUserInfo = None,
        ):
        self._stray_cat = stray_cat
        self.chat_id = chat_id

        super().__init__(user_data)


    def __send_ws_json(self, data: Any):
        return self._stray_cat.__send_ws_json(data)
    
    def send_ws_message(self, content: str, msg_type: MSG_TYPES = "notification"):
        # Only for "common" sons
        if self.chat_id != "default":
            content = {
                "content": content,
                "chat_id": self.chat_id
            }
        return self._stray_cat.send_ws_message(content, msg_type)

    def __repr__(self):
        return f"SonStrayCat(user_id={self.user_id}, chat_id={self.chat_id})"
    
    def __str__(self) -> str:
        return f"SonStrayCat of {self.user_id} in chat {self.chat_id}"
    
    def send_chat_message(self, message: Union[str, CatMessage], save=False):
        """Sends a chat message to the user using the active WebSocket connection.

        In case there is no connection the message is skipped and a warning is logged

        Args:
            message (Union[str, CatMessage]): message to send
            save (bool, optional): Save the message in the conversation history. Defaults to False.
        """

        if isinstance(message, str):
            why = self.__build_why()
            message = CatMessage(text=message, user_id=self.user_id, why=why, chat_id=self.chat_id)

        if save:
            self.working_memory.update_history(
                message
            )

        self.__send_ws_json(message.model_dump())

    def __call__(self, message_dict):
        output = super().__call__(message_dict)

        if isinstance(output, CatMessage):
            output.chat_id = self.chat_id

        return output
    
    @property
    def agent_id(self):
        return self.working_memory.user_message_json.agent_id
    
    def is_default_agent(self):
        return self.agent_id == "default"

    def get_instructions(self):
        agent = agent_manager.get_agent(self.agent_id)
        if agent is not None:
            agent.cast()
            return agent.instructions if not self.is_default_agent() else None
        
        return None

    # Cache methods
    def __build_cache_key(self):
        """Build the cache key for the user_id"""
        
        # Build the cache key
        key_result = ""
        for key, is_attr in self.cache_keys:
            if is_attr and hasattr(self, key):
                key_result += f"{getattr(self, key)}_"
            else:
                key_result += f"{key}_"

        # Remove the last underscore
        return key_result

    def load_working_memory_from_cache(self):
        """Load the working memory from the cache."""
        
        self.working_memory = \
            self.cache.get_value(f"{self.__build_cache_key()}_working_memory") or WorkingMemory()
        
    def update_working_memory_cache(self):
        """Update the working memory in the cache."""

        updated_cache_item = CacheItem(f"{self.__build_cache_key()}_working_memory", self.working_memory, -1)
        self.cache.insert(updated_cache_item)