import time
from typing import Any, Dict, List, Optional, Union
import uuid

from fastapi import WebSocket
from cat.auth.permissions import AuthUserInfo

from cat.convo.messages import CatMessage, UserMessage
from cat.log import log

from cat.looking_glass.cheshire_cat import CheshireCat

from cat.looking_glass.stray_cat import StrayCat
from cat.memory.working_memory import WorkingMemory
from cat.cache.cache_item import CacheItem

from cat.looking_glass.stray_cat import MSG_TYPES

from cat.memory.vector_memory_collection import VectorMemoryCollection
from cat.rabbit_hole import RabbitHole

from cat.plugins.multicat.decorators import option, get_true_class
from cat.plugins.multicat.types import Agent

# from .types import Agent

from cat.utils import singleton


# NOTE: If you don't have the option decorator, this is all useless

# Logic:
## 1. Create the SonStrayCat
## 2. Create the Father
## 3. hook: before_cat_stores_episodic_memory
## 4. hook: before_cat_recalls_episodic_memories
### Endpoints:
#### POST /chat/{chat_id}/message

@option(UserMessage)
class UserMessageChat(UserMessage):
    """Message class with chat and agent identification"""

    chat_id: Optional[str] = "default"
    agent_id: Optional[str] = "default"

@option(CatMessage)
class CatMessageChat(CatMessage):
    chat_id: Optional[str] = "default"


class CommonStrayCat():
    """
    This is the Common StrayCat
    
    - control for agents
    - control for cache with chat_id

    """

    def get_agent_by_id(self, agent_id):
        if agent_id in self.agents:
            return self.agents[agent_id]
        
        return None
    
    @property
    def agents(self) -> Dict[str, Agent]:
        return CheshireCat().agents
    
    def create_agent(self, **kwargs):
        id = kwargs.pop("id", "default")

        # Generate a new agent id if not specified
        if id == "default":
            new_agent_id = str(uuid.uuid4())
        else:
            new_agent_id = id

            # If already exists, update the agent
            if new_agent_id in self.agents:
                self.agents[new_agent_id] = Agent(id=new_agent_id, **kwargs)
                return self.agents[new_agent_id]

        # Check if the agent already exists
        while new_agent_id in self.agents:
            new_agent_id = str(uuid.uuid4())

        agent = Agent(id=new_agent_id, **kwargs)
        self.agents[new_agent_id] = agent

        return agent


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
            stray_cat: "FatherStrayCat",
            user_data: AuthUserInfo = None,
        ):
        self._stray_cat = stray_cat
        self.chat_id = chat_id

        super().__init__(user_data)


    def __send_ws_json(self, data: Any):
        log.error(f"Sending data to chat {self.chat_id}")
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
        if self.agent_id in self.agents and not self.is_default_agent():
            return self.agents[self.agent_id].instructions
        
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

# Adapt the StrayCat to curate the SonStrayCat (the perfect father)
@option(StrayCat)
class FatherStrayCat(StrayCat, CommonStrayCat):
    bevoled_son_chat_id = "default"

    def __init__(
        self,
        user_data: AuthUserInfo
    ):
        log.warning("FatherStrayCat created")
        
        # user data
        self.__user_id = user_data.name # TODOV2: use id
        self.__user_data = user_data

        self.stray_sons: Dict[str, SonStrayCat] = {}

        super().__init__(user_data)

    def create_son(self, chat_id: str):
        """Create a new son"""

        self.stray_sons[chat_id] = SonStrayCat(
            chat_id,
            self,
            self.user_data,
        )
        
        return self.stray_sons[chat_id]
    
    def load_working_memory_from_cache(self):
        """Load the working memory of bevoled son from the cache"""
        return self.get_beloved_son().load_working_memory_from_cache()
    
    def update_working_memory_cache(self):
        """Update the working memory of bevoled son in the cache"""
        return self.get_beloved_son().update_working_memory_cache()
    
    @property
    def chat_id(self):
        """Return the chat id of the beloved son"""
        return self.bevoled_son_chat_id

    @property
    def working_memory(self):
        """Return the working memory of the beloved son"""
        return self.get_beloved_son().working_memory
    
    @working_memory.setter
    def working_memory(self, value):
        """Set the working memory of the beloved son"""
        self.get_beloved_son().working_memory = value

    @property
    def chat_list(self) -> List:
        """Return the list of chat ids"""
        return list(self.stray_sons.keys())
    
    def create_bevoled_son(self):
        """Create the beloved son"""
        return self.create_son(self.bevoled_son_chat_id)
    
    def get_son(self, chat_id: str):
        """Get the son"""
        if chat_id not in self.stray_sons:
            return self.create_son(chat_id)
        
        return self.stray_sons[chat_id]
    
    def get_beloved_son(self):
        """Get the beloved son"""
        return self.get_son(self.bevoled_son_chat_id)

    # @property
    # def working_memory(self) -> WorkingMemory:
    #     """Return the beloved son"""
    #     return self.get_beloved_son().working_memory

    def __build_why(self):
        return self.get_beloved_son().__build_why()
    
    def __call__(self, message_dict):
        log.error(f"FatherStrayCat called with {message_dict}")
        
        message_dict["user_id"] = self.user_id

        user_message = UserMessageChat.model_validate(message_dict)
        chat_id = user_message.chat_id

        # now recall son
        return self.get_son(chat_id)(message_dict)
    
    def __repr__(self):
        return f"FatherStrayCat(user_id={self.user_id})"
    
    def __str__(self) -> str:
        return f"FatherStrayCat of {self.user_id}"
    
    @property
    def user_id(self) -> str:
        """The user's id.
        
        Returns
        -------
        user_id : str
            Current user's id.
        """
        return self.__user_id
    
    @property
    def user_data(self) -> AuthUserInfo:
        """`AuthUserInfo` object containing user data.

        Returns
        -------
        user_data : AuthUserInfo
            Current user's data.
        """
        return self.__user_data
    
    @property
    def _llm(self):
        """Instance of langchain `LLM`.
        Only use it if you directly want to deal with langchain, prefer method `cat.llm(prompt)` otherwise.
        """
        return CheshireCat()._llm

    @property
    def embedder(self):
        """Langchain `Embeddings` object.

        Returns
        -------
        embedder : langchain `Embeddings`
            Langchain embedder to turn text into a vector.


        Examples
        --------
        >>> cat.embedder.embed_query("Oh dear!")
        [0.2, 0.02, 0.4, ...]
        """
        return CheshireCat().embedder

    @property
    def memory(self):
        """Gives access to the long term memory, containing vector DB collections (episodic, declarative, procedural).

        Returns
        -------
        memory : LongTermMemory
            Long term memory of the Cat.


        Examples
        --------
        >>> cat.memory.vectors.episodic
        VectorMemoryCollection object for the episodic memory.
        """
        return CheshireCat().memory

    @property
    def rabbit_hole(self):
        """Gives access to the `RabbitHole`, to upload documents and URLs into the vector DB.

        Returns
        -------
        rabbit_hole : RabbitHole
            Module to ingest documents and URLs for RAG.


        Examples
        --------
        >>> cat.rabbit_hole.ingest_file(...)
        """
        return CheshireCat().rabbit_hole

    @property
    def mad_hatter(self):
        """Gives access to the `MadHatter` plugin manager.

        Returns
        -------
        mad_hatter : MadHatter
            Module to manage plugins.


        Examples
        --------

        Obtain the path in which your plugin is located
        >>> cat.mad_hatter.get_plugin().path
        /app/cat/plugins/my_plugin

        Obtain plugin settings
        >>> cat.mad_hatter.get_plugin().load_settings()
        {"num_cats": 44, "rows": 6, "remainder": 0}
        """
        return CheshireCat().mad_hatter

    @property
    def main_agent(self):
        """Gives access to the default main agent.
        """
        return CheshireCat().main_agent

    @property
    def white_rabbit(self):
        """Gives access to `WhiteRabbit`, to schedule repeatable tasks.

        Returns
        -------
        white_rabbit : WhiteRabbit
            Module to manage cron tasks via `APScheduler`.

        Examples
        --------
        Send a websocket message after 30 seconds
        >>> def ring_alarm_api():
        ...     cat.send_chat_message("It's late!")
        ...
        ... cat.white_rabbit.schedule_job(ring_alarm_api, seconds=30)
        """
        return CheshireCat().white_rabbit
    
    @property
    def cache(self):
        """Gives access to internal cache."""
        return CheshireCat().cache


@option(VectorMemoryCollection)
class MyVectorMemoryCollection(VectorMemoryCollection):
    def update_points_by_metadata(self, points_ids=[], metadata={}):
        """
        Aggiorna i metadati dei punti specificati nella collezione vettoriale.
        
        Args:
            points_ids (list): Lista degli ID dei punti da aggiornare
            metadata (dict): Dizionario contenente i metadati da applicare
            
        Returns:
            dict: Risultato dell'operazione di aggiornamento
        """
        # Aggiorna i metadati dei punti attraverso il client
        update_result = self.client.set_payload(
            collection_name=self.collection_name,
            points=points_ids,
            payload=metadata,
        )
        return update_result
    
@option(RabbitHole)
@singleton
class MyRabbitHole(get_true_class(RabbitHole)):
    def _send_progress_notification(self, cat, perc_read, file_source):
        """Helper method to send progress notification"""
        cat.send_ws_message(
            content={
                "status": "progress",
                "perc_read": perc_read,
                "source": file_source,
                "type": "doc-reading-progress",
        }, msg_type="json-notification")

    def _send_completion_notification(self, cat, file_source):
        """Helper method to send completion notification"""
        cat.send_ws_message(
            content={
                "status": "done",
                "perc_read": 100,
                "source": file_source,
                "type": "doc-reading-progress",
            }, msg_type="json-notification")

    def store_documents(self, cat, docs, source, metadata):
        time_last_notification = time.time()
        time_interval = 10  # a notification every 10 secs
        stored_points = []
        file_source = metadata.get("file_id", source)

        log.info(f"Preparing to memorize {len(docs)} vectors")
        
        # hook the docs before they are stored in the vector memory
        docs = cat.mad_hatter.execute_hook(
            "before_rabbithole_stores_documents", docs, cat=cat
        )

        for d, doc in enumerate(docs):
            perc_read = int(d / len(docs) * 100)
            
            # Send periodic text updates
            if time.time() - time_last_notification > time_interval:
                time_last_notification = time.time()
                read_message = f"Read {perc_read}% of {source}"
                cat.send_ws_message(read_message)
                log.warning(read_message)

            # Send detailed progress update
            self._send_progress_notification(cat, perc_read, file_source)

            # Process document
            doc.metadata.update({
                "source": source,
                "when": time.time()
            })
            # Add custom metadata
            for k,v in metadata.items():
                doc.metadata[k] = v

            doc = cat.mad_hatter.execute_hook(
                "before_rabbithole_insert_memory", doc, cat=cat
            )
            
            inserting_info = f"{d + 1}/{len(docs)}):    {doc.page_content}"
            if doc.page_content != "":
                doc_embedding = cat.embedder.embed_documents([doc.page_content])
                stored_point = cat.memory.vectors.declarative.add_point(
                    doc.page_content,
                    doc_embedding[0],
                    doc.metadata,
                )
                stored_points.append(stored_point)
                log.info(f"Inserted into memory ({inserting_info})")
            else:
                log.info(f"Skipped memory insertion of empty doc ({inserting_info})")

            # wait a little to avoid APIs rate limit errors
            time.sleep(0.05)

        # hook the points after they are stored in the vector memory
        cat.mad_hatter.execute_hook(
            "after_rabbithole_stored_documents", source, stored_points, cat=cat
        )

        # Send completion notifications
        finished_reading_message = f"Finished reading {source}, I made {len(docs)} thoughts on it."
        cat.send_ws_message(finished_reading_message)
        self._send_completion_notification(cat, file_source)
        log.warning(f"Done uploading {source}")


msg_types = list(MSG_TYPES.__dict__["__args__"])
msg_types.append("json-notification")
MSG_TYPES.__dict__["__args__"] = tuple(msg_types)