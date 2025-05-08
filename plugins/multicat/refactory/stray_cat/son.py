from typing import Any, List, Union
import tiktoken

from cat.auth.permissions import AuthUserInfo

from cat.convo.messages import CatMessage, EmbedderModelInteraction

from cat.looking_glass.stray_cat import StrayCat

from cat.memory.working_memory import WorkingMemory
from cat.looking_glass.stray_cat import MSG_TYPES

from cat.cache.cache_item import CacheItem

from cat import utils
from cat.log import log

from cat.plugins.multicat.refactory.stray_cat.common import CommonStrayCat
from cat.plugins.multicat.agents.cat_agents.main_agent import MainAgentLimited

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
        return self.working_memory.user_message_json.agent_id or "default"

    @property
    def agent(self):
        """Return the agent of the son"""
        return agent_manager.get_agent(self.agent_id).cast()

    def is_default_agent(self):
        return self.agent_id == "default"

    def get_instructions(self):
        agent = agent_manager.get_agent(self.agent_id)
        if agent is not None:
            agent = agent.cast()
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

    @property
    def history(self):
        return self.working_memory.history
    
    @history.setter
    def history(self, value):
        self.working_memory.history = value
        self.update_working_memory_cache()

    @property
    def main_agent(self):
        """Return the main agent of the son"""
        return MainAgentLimited.get_for_agent(self.agent) if not self.is_default_agent() else super().main_agent

    def recall_relevant_memories_to_working_memory(self, query=None):
        """Retrieve context from memory.

        The method retrieves the relevant memories from the vector collections that are given as context to the LLM.
        Recalled memories are stored in the working memory.

        Parameters
        ----------
        query : str, optional
            The query used to make a similarity search in the Cat's vector memories.  
            If not provided, the query will be derived from the last user's message.

        Examples
        --------
        Recall memories from custom query
        >>> cat.recall_relevant_memories_to_working_memory(query="What was written on the bottle?")

        Notes
        -----
        The user's message is used as a query to make a similarity search in the Cat's vector memories.
        Five hooks allow to customize the recall pipeline before and after it is done.

        See Also
        --------
        cat_recall_query
        before_cat_recalls_memories
        before_cat_recalls_episodic_memories
        before_cat_recalls_declarative_memories
        before_cat_recalls_procedural_memories
        after_cat_recalls_memories
        """

        recall_query = query

        if query is None:
            # If query is not provided, use the user's message as the query
            recall_query = self.working_memory.user_message_json.text

        # We may want to search in memory
        recall_query = self.mad_hatter.execute_hook(
            "cat_recall_query", recall_query, cat=self
        )
        log.info(f"Recall query: '{recall_query}'")

        # Embed recall query
        recall_query_embedding = self.embedder.embed_query(recall_query)
        self.working_memory.recall_query = recall_query

        # keep track of embedder model usage
        self.working_memory.model_interactions.append(
            EmbedderModelInteraction(
                prompt=[recall_query],
                source=utils.get_caller_info(skip=1),
                reply=recall_query_embedding, # TODO: should we avoid storing the embedding?
                input_tokens=len(tiktoken.get_encoding("cl100k_base").encode(recall_query)),
            )
        )

        # hook to do something before recall begins
        self.mad_hatter.execute_hook("before_cat_recalls_memories", cat=self)

        # Setting default recall configs for each memory
        # TODO: can these data structures become instances of a RecallSettings class?
        default_episodic_recall_config = {
            "embedding": recall_query_embedding,
            "k": 3,
            "threshold": 0.7,
            "metadata": {"source": self.user_id},
        }

        default_declarative_recall_config = {
            "embedding": recall_query_embedding,
            "k": 3,
            "threshold": 0.7,
            "metadata": {},
        }

        default_procedural_recall_config = {
            "embedding": recall_query_embedding,
            "k": 3,
            "threshold": 0.7,
            "metadata": {},
        }

        # hooks to change recall configs for each memory
        recall_configs = [
            self.mad_hatter.execute_hook(
                "before_cat_recalls_episodic_memories",
                default_episodic_recall_config,
                cat=self,
            ),
            self.mad_hatter.execute_hook(
                "before_cat_recalls_declarative_memories",
                default_declarative_recall_config,
                cat=self,
            ),
            self.mad_hatter.execute_hook(
                "before_cat_recalls_procedural_memories",
                default_procedural_recall_config,
                cat=self,
            ),
        ]

        memory_types = self.mad_hatter.execute_hook(
            "get_memory_type_keys",
            list(self.memory.vectors.collections.keys()),
            cat=self
        )

        for config, memory_type in zip(recall_configs, memory_types):
            memory_key = f"{memory_type}_memories"

            # recall relevant memories for collection
            vector_memory = getattr(self.memory.vectors, memory_type)
            memories = vector_memory.recall_memories_from_embedding(**config)

            setattr(
                self.working_memory, memory_key, memories
            )  # self.working_memory.procedural_memories = ...

        # hook to modify/enrich retrieved memories
        self.mad_hatter.execute_hook("after_cat_recalls_memories", cat=self)

    @property
    def _llm(self):
        if self.is_default_agent():
            return super()._llm
        
        llm_name = self.agent.llm_name
        if llm_name is None:
            return super()._llm

        llm = self.get_llm_by_name(llm_name, database_only=False, save=True, cast=True)
        if llm is None:
            return super()._llm

        return llm
