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
from cat.looking_glass.stray_cat import MSG_TYPES
from cat.memory.vector_memory_collection import VectorMemoryCollection
from cat.rabbit_hole import RabbitHole
from cat.looking_glass.stray_cat import MSG_TYPES

from cat.plugins.multicat.decorators import option, get_true_class
from cat.plugins.multicat.types import Agent

# from .types import Agent

from cat.utils import singleton


# NOTE: If you don't have option, this is all useless

# Logic:
## first we create the SonStrayCat
## after we create the Father
## hook: before_cat_stores_episodic_memory
## hook: before_cat_recalls_episodic_memories
### Endpoints:
#### POST /chat/{chat_id}/message

@option(UserMessage)
class UserMessageChat(UserMessage):
    chat_id: Optional[str] = "default"
    agent_id: Optional[str] = "default"

@option(CatMessage)
class CatMessageChat(CatMessage):
    chat_id: Optional[str] = "default"

stray_cat_attr = {k: v for k, v in StrayCat.__dict__.items()}
MyStrayCat: StrayCat = type("MyStrayCat", StrayCat.__bases__, stray_cat_attr)

# A perfect son
class SonStrayCat(MyStrayCat):
    """
    This is the Very StrayCat

    chat_id: str is the chat_id of the chat
    stray_cat: StrayCat is the stray_cat object (the father)

    *other: args and kwargs are the same as StrayCat
    """
    def __init__(
            self,
            chat_id,
            stray_cat: StrayCat,  # it's a lie!
            user_id: str,
            main_loop,
            user_data: AuthUserInfo = None,
            ws: WebSocket = None,
        ):
        self._stray_cat = stray_cat
        self.chat_id = chat_id

        super().__init__(user_id, main_loop, user_data, ws)

        # self.working_memory = WorkingMemory()

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
        if self.__ws is None:
            log.warning(f"No websocket connection is open for user {self.user_id}")
            return

        if isinstance(message, str):
            why = self.__build_why()
            message = CatMessage(text=message, user_id=self.user_id, why=why, chat_id=self.chat_id)

        if save:
            self.working_memory.update_conversation_history(
                who="AI", text=message["text"], why=message["why"]
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

        # Check if the agent already exists
        while new_agent_id in self.agents:
            new_agent_id = str(uuid.uuid4())

        agent = Agent(id=new_agent_id, **kwargs)
        self.agents[new_agent_id] = agent

        return agent
    
    def get_instructions(self):        
        if self.agent_id in self.agents and not self.is_default_agent():
            return self.agents[self.agent_id].instructions
        
        return None

# Adapt the StrayCat to curate the SonStrayCat (the perfect father)
@option(StrayCat)
class FatherStrayCat(StrayCat):
    def __init__(
        self,
        user_id: str,
        main_loop,
        user_data: AuthUserInfo = None,
        ws: WebSocket = None,
    ):
        log.warning("FatherStrayCat created")
        
        super().__init__(user_id, main_loop, user_data, ws)

        self.__user_id = user_id
        self.__user_data = user_data

        # # attribute to store ws connection
        self.__ws = ws

        self.__main_loop = main_loop

        self.stray_sons: Dict[str, SonStrayCat] = {}

        # self.working_memory = property(self._get_working_memory)
        # log.error(f"Working memory: {self.working_memory}")

    def create_son(self, chat_id: str):
        """Create a new son"""

        self.stray_sons[chat_id] = SonStrayCat(
            chat_id,
            self,
            super().user_id,
            self.main_loop,
            self.user_data,
            self.ws
        )
        
        return self.stray_sons[chat_id]
    
    @property
    def working_memory(self):
        return self.get_beloved_son().working_memory
    
    @working_memory.setter
    def working_memory(self, value):
        pass

    @property
    def chat_list(self) -> List:
        return list(self.stray_sons.keys())
    
    def create_bevoled_son(self):
        """Create the beloved son"""
        return self.create_son("default")
    
    def get_son(self, chat_id: str):
        """Get the son"""
        if chat_id not in self.stray_sons:
            return self.create_son(chat_id)
        
        return self.stray_sons[chat_id]
    
    def get_beloved_son(self):
        """Get the beloved son"""
        return self.get_son("default")

    # @property
    # def working_memory(self) -> WorkingMemory:
    #     """Return the beloved son"""
    #     return self.get_beloved_son().working_memory

    def __build_why(self):
        return self.get_beloved_son().__build_why()
    
    def __call__(self, message_dict):
        log.error(f"FatherStrayCat called with {message_dict}")
        user_message = UserMessageChat.model_validate(message_dict)
        chat_id = user_message.chat_id

        # now recall son
        return self.get_son(chat_id)(message_dict)
    
    def __repr__(self):
        return f"FatherStrayCat(user_id={self.user_id})"
    
    def __str__(self) -> str:
        return f"FatherStrayCat of {self.user_id}"
    
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

        # Check if the agent already exists
        while new_agent_id in self.agents:
            new_agent_id = str(uuid.uuid4())

        agent = Agent(id=new_agent_id, **kwargs)
        self.agents[new_agent_id] = agent

        return agent
    
    @property
    def main_loop(self):
        return self.__main_loop
    
    @property
    def user_data(self):
        return self.__user_data
    
    @property
    def user_id(self):
        return self.__user_id
    
    @property
    def ws(self):
        return self.__ws
    
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
    def _send_progress_notification(self, stray, perc_read, file_source):
        """Helper method to send progress notification"""
        stray.send_ws_message(
            content={
                "status": "progress",
                "perc_read": perc_read,
                "source": file_source,
                "type": "doc-reading-progress",
        }, msg_type="json-notification")

    def _send_completion_notification(self, stray, file_source):
        """Helper method to send completion notification"""
        stray.send_ws_message(
            content={
                "status": "done",
                "perc_read": 100,
                "source": file_source,
                "type": "doc-reading-progress",
            }, msg_type="json-notification")

    def store_documents(self, stray, docs, source, metadata):
        time_last_notification = time.time()
        time_interval = 10  # a notification every 10 secs
        stored_points = []
        file_source = metadata.get("file_id", source)

        log.info(f"Preparing to memorize {len(docs)} vectors")
        
        # hook the docs before they are stored in the vector memory
        docs = stray.mad_hatter.execute_hook(
            "before_rabbithole_stores_documents", docs, cat=stray
        )

        for d, doc in enumerate(docs):
            perc_read = int(d / len(docs) * 100)
            
            # Send periodic text updates
            if time.time() - time_last_notification > time_interval:
                time_last_notification = time.time()
                read_message = f"Read {perc_read}% of {source}"
                stray.send_ws_message(read_message)
                log.warning(read_message)

            # Send detailed progress update
            self._send_progress_notification(stray, perc_read, file_source)

            # Process document
            doc.metadata.update({
                "source": source,
                "when": time.time()
            })
            # Add custom metadata
            for k,v in metadata.items():
                doc.metadata[k] = v

            doc = stray.mad_hatter.execute_hook(
                "before_rabbithole_insert_memory", doc, cat=stray
            )
            
            inserting_info = f"{d + 1}/{len(docs)}):    {doc.page_content}"
            if doc.page_content != "":
                doc_embedding = stray.embedder.embed_documents([doc.page_content])
                stored_point = stray.memory.vectors.declarative.add_point(
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
        stray.mad_hatter.execute_hook(
            "after_rabbithole_stored_documents", source, stored_points, cat=stray
        )

        # Send completion notifications
        finished_reading_message = f"Finished reading {source}, I made {len(docs)} thoughts on it."
        stray.send_ws_message(finished_reading_message)
        self._send_completion_notification(stray, file_source)
        log.warning(f"Done uploading {source}")


msg_types = list(MSG_TYPES.__dict__["__args__"])
msg_types.append("json-notification")
MSG_TYPES.__dict__["__args__"] = tuple(msg_types)