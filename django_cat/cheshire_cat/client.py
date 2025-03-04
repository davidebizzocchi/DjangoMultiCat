import mimetypes
from typing import Iterable, Dict, List, Union
from icecream import ic
# from users.models import UserProfile
import requests
import time
from cheshire_cat.decorators import wait_cat, HOST, PORT, wait_for_cat
import json
from queue import Queue
from decouple import config
import io
import uuid

from cheshire_cat.types import AgentRequest, CatMessage, ChatHistoryMessage, ChatToken, ChatHistory, GenericMessage, Notification, DocReadingProgress
from cheshire_cat.types import Agent as AgentComplete
from openai import OpenAI

import cheshire_cat_api as ccat

from gtts import gTTS
from bs4 import BeautifulSoup
import markdown2

from cheshire_cat.custom_objects import CatClient
import tiktoken

from django.conf import settings


CatConfig = ccat.Config
END_STREAM = object()

class Cat(CatClient):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        config = kwargs.get('config')
        if not config:
            raise ValueError("Config is required")
        
        user_id = config.user_id
        
        if user_id not in cls._instances:
            wait_for_cat()
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[user_id] = instance
            # cls._ref_counts[user_id] = 0  # Initialize counter
        
        # cls._ref_counts[user_id] += 1  # Increment counter
        return cls._instances[user_id]

    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_initialized') or not self._initialized:
            # str is chat_id
            self._chat_queues: Dict[str, Queue] = {}
            self._message_contents: Dict[str, CatMessage] = {}
            self._stream_active: Dict[str, bool] = {}
            self._is_startup = False
            self.AUDIO_MAX_SIZE = 25 * 1024 * 1024  # 25MB in bytes
            
            super().__init__(on_message=self.on_message, *args, **kwargs)

            self._llm = OpenAI(
                base_url=settings.LLM_PROVIDER_API_URL if settings.LLM_PROVIDER_API_URL != "" else None,
                api_key=settings.LLM_PROVIDER_API_KEY
            )
            self.startup()
            
            self._notification_handlers: Dict[str, callable] = {}
            self._initialized = True

    def _check_ws_connection(self):
        if not self.is_ws_connected:
            self.startup()

    def connect_ws(self):
        if not self.is_ws_connected:
            return super().connect_ws()

    def startup(self):
        ic(self.is_ws_connected)
        if self.is_ws_connected or self._is_startup:
            return self
        
        self.connect_ws()
        self._is_startup = True

        counter = 0
        while not self.is_ws_connected:
            time.sleep(0.2)
            counter += 1

            if self._is_startup:
                break

            if counter == 100:
                raise TimeoutError("Cannot connect to the websocket")

        return self
    
    def count_token(self, message: str):
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(message))
    
    def chat_completition(self, message: str):
        """Send a message to the completion chat"""
        self.send(message=message, chat_id="completition")

        return "completition"

    def send(self, message, chat_id="default", agent_id=None, *args, **kwargs):
        from chat.models import Chat
        """Send prompt to ws with specific chat_id"""
        self._reset_new_message(chat_id)
        self._check_ws_connection()

        # Retrieve the agent_id if not passed
        if agent_id is None:
            agent_id = Chat.objects.select_related("agent").only("agent__agent_id").get(chat_id=chat_id).agent.agent_id

        return super().send(message, chat_id=chat_id, agent_id=agent_id, *args, **kwargs)

    def on_message(self, message):
        """Callback for message received"""

        msg_json = json.loads(message)
        self._on_message(msg_json)

    def _reset_new_message(self, chat_id="default"):
        """Reset message state for a specific chat"""
        
        self._chat_queues[chat_id] = Queue()
        
        self._message_contents[chat_id] = None
        self._stream_active[chat_id] = True

    def _on_message(self, message: dict):
        """Handle messages for specific chats"""
        msg_type = message.get("type", None)
        chat_id = message.get("chat_id", "default")
        
        if msg_type == "chat_token":
            message = message.get("content", {})
            content = message.get("content", "")
            chat_id = message.get("chat_id", "default")

            stream_message = ChatToken(text=content, chat_id=chat_id)

            if self._stream_active.get(chat_id, False):
                self._chat_queues[chat_id].put(stream_message)
        
        elif msg_type == "chat":
            self._message_contents[chat_id] = CatMessage(**message)
            self.end_stream(chat_id)
        
        elif msg_type == "json-notification":
            content = message.get("content", {})
            if content.get("type") == "doc-reading-progress":
                progress = DocReadingProgress(**content)

                # Notify the registered handlers with their arguments
                handlers = list(self._notification_handlers.values())
                for handler in handlers:
                    handler(progress)
        
        else:
            # Handle generic messages
            generic_message = GenericMessage(**message)
            # You can add specific handling for other message types here
            ic(f"Received generic message: {generic_message}")

            # Stop all streams
            if generic_message.type == "error":
                self.end_stream(chat_id)

    def end_stream(self, chat_id: str = "default"):
        """End stream for specific chat"""
        if chat_id in self._stream_active:
            self._stream_active[chat_id] = False
            self._chat_queues[chat_id].put(END_STREAM)

    def _stream(self, chat_id):
        """Stream messages for specific chat"""
        
        while self._stream_active.get(chat_id, False):
            chat_queque = self._chat_queues[chat_id]
            try:
                token = chat_queque.get(block=True)

                if token is END_STREAM:  # termination signal
                    break
                yield token

                continue  # Continue listening if the queue is empty
            except Exception as e:
                ic(f"Stream error for chat {chat_id}: {e}")
                break

    def stream(self, chat_id: str = "default") -> Iterable[ChatToken]:
        """Stream messages for specific chat"""

        if chat_id not in self._stream_active:
            yield f"Error: {chat_id} this chat is not active"
            return
        
        # Change here: yield from instead of a simple call
        yield from self._stream(chat_id)

    def get_message_content(self, chat_id: str = "default") -> CatMessage:
        return self._message_contents.get(chat_id)
    
    def wait_message_content(self, chat_id: str = "default") -> CatMessage:
        while self._message_contents.get(chat_id) is None:
            time.sleep(0.1)

            if not self._stream_active.get(chat_id):
                return None
        return self._message_contents[chat_id]
    
    def _transcribe(self, audio_bytes, language="it"):
        start = time.time()
        transcription = self._llm.audio.transcriptions.create(
            file=("temp.wav", audio_bytes),
            model=settings.LLM_MODEL_AUDIO_TRANSCRIPTION_ID,
            language=language,
            prompt="Transcribe the user's message",
            response_format="json"
        )
        ic("time", time.time() - start, transcription)
        return transcription.text.strip()
    
    def transcribe(self, audio_bytes):
        # Get file size
        audio_bytes.seek(0, 2)  # Seek to end
        file_size = audio_bytes.tell()
        audio_bytes.seek(0)  # Reset to start

        # If file is smaller than MAX_SIZE, process normally
        if file_size <= self.AUDIO_MAX_SIZE:
            return self._transcribe(audio_bytes.read())

        # For larger files, split and process in chunks
        full_text = []
        chunk_size = self.AUDIO_MAX_SIZE
        
        while True:
            chunk = audio_bytes.read(chunk_size)
            if not chunk:
                break

            # Create a temporary file-like object for the chunk
            chunk_bytes = io.BytesIO(chunk)

            full_text.append(self._transcribe(chunk_bytes))

        return " ".join(full_text)
    
    def parse_markdown(self, text):
        return BeautifulSoup(markdown2.markdown(text), "html.parser").get_text()
    
    def _speak_gtts(self, text):
        return gTTS(
            text=self.parse_markdown(text),
            lang=settings.LANGUAGE_CODE.split("-")[0].lower(),
        ).write_to_fp(io.BytesIO())

    def _speak(self, text):
        if settings.LLM_MODEL_AUDIO_ID == "gtts":
            return self._speak_gtts(text)

        return None
    
    def speak(self, text):
        return self._speak(text)
    
    def get_collections_name(self, name: str) -> Iterable[str]:
        for collection in self.memory.get_collections()["collections"]:
            yield collection["name"]

    def wipe_chat_episodic(self, chat_id: str):
        # it is correct that the key is "chat"!
        return self.memory.wipe_memory_points_by_metadata(
            collection_id="episodic",
            body={"chat": chat_id}
        )

    def delete_chat(self, chat_id: str):
        self.wipe_chat_episodic(chat_id)
        return self.memory.delete_working_memory(chat_id)
    
    def wipe_chat(self, chat_id: str):
        self.wipe_chat_episodic(chat_id)
        return self.memory.wipe_conversation_history_by_chat(chat_id)
    
    def get_chat_history(self, chat_id: str):
        response = self.memory.get_working_memory(chat_id)
        if "history" in response:
            return ChatHistory(messages=[
                ChatHistoryMessage(**msg) for msg in response["history"]
            ])
        return ChatHistory()

    def get_chat_list(self):
        return self.memory.get_working_memories_list()

    def register_notification_handler(self, handler, *handler_args, **handler_kwargs) -> str:
        """
        Register a handler for notifications and return its ID
        
        Args:
            handler: Function that receives a notification
            *handler_args: Positional arguments to pass to the handler
            **handler_kwargs: Keyword arguments to pass to the handler
            
        Returns:
            str: Unique ID of the registered handler
        """
        handler_id = str(uuid.uuid4())
        self._notification_handlers[handler_id] = handler
        return handler_id

    def unregister_notification_handler(self, handler_id: str):
        """
        Remove a handler given its ID
        
        Args:
            handler_id: ID of the handler to remove
        """
        if handler_id in self._notification_handlers:
            del self._notification_handlers[handler_id]

    def unregister_all_notification_handlers(self):
        """Removes all registered handlers"""
        self._notification_handlers.clear()

    def _cleanup_old_notifications(self):
        """Removes notifications older than TTL seconds"""
        current_time = time.time()
        while self._notifications and (current_time - self._notifications[0].received_at) > self._notification_ttl:
            self._notifications.popleft()

    def _add_notification(self, notification: Notification):
        """Adds a new notification and cleans up old ones"""
        self._cleanup_old_notifications()
        self._notifications.append(notification)

    def get_recent_notifications(self):
        """Returns recent notifications after cleaning up old ones"""
        self._cleanup_old_notifications()
        return list(self._notifications)
    
    def upload_file(self, file, metadata: Dict, chunk_size=None, chunk_overlap=None):
        url =  f"http://{HOST}:{PORT}/rabbithole/"
        
        with open(file.file.path.absolute(), "rb") as f:
            files = {"file": (
                str(file.file.path.name),  # Use the file_id with the extension
                f,
                mimetypes.guess_type(file.file.path.absolute())[0]
            )}

            payload = {
                "metadata": json.dumps(metadata),
                "chunk_overlap": chunk_overlap,
                "chunk_size": chunk_size,
            }

            return requests.post(
                url=url,
                files=files,
                data=payload,
                headers={
                    "user_id": file.userprofile.cheshire_id  # Add the user_id in the header
                },
            ).json()
    
    def delete_file(self, file):
        return self.memory.wipe_memory_points_by_metadata(
            collection_id="declarative",
            body={
                "file_id": str(file.file_id),
            }
        )

    def get_file_chats(self, file) -> List[str]:
        """Get all chats using a specific file through its libraries
        
        Args:
            file: File instance to check
            
        Returns:
            List[str]: List of chat IDs using this file
        """
        from chat.models import Chat

        return list(
            Chat.objects.filter(
                libraries__associations__file=file  # Navigate through the relationships
            ).values_list(
                'chat_id', flat=True
            ).distinct()
        )

    def update_file_chats(self, file) -> dict:
        """Update the chats associated with a file in the memory
        
        Args:
            file: File instance to update
            
        Returns:
            dict: Response from the API with update status
        """
        chat_ids = self.get_file_chats(file)
                
        metadata = {
            "search": {"file_id": str(file.file_id)},
            "update": {"chats_id": chat_ids}
        }
        
        return self.memory.update_points_metadata(
            collection_id="declarative",
            search=metadata["search"], 
            update=metadata["update"]
        )

    def get_file_metadata(self, file) -> dict:
        """Get all memory points for a specific file
        
        Args:
            file_id: ID of the file to search for
            
        Returns:
            dict: Memory points containing the file metadata
        """
        return self.memory.get_points_by_metadata(
            collection_id="declarative",
            metadata={"file_id": str(file.file_id)}
        )

    def edit_file_chats(self, file, chat_ids: List[str], mode: str = "add", collection_id: str = "declarative"):
        """
        Update chat_ids in file memories metadata
        :param file: File instance to update
        :param chat_ids: List of chat IDs to add/remove
        :param mode: 'add' to add chat_ids, 'remove' to remove them
        """

        if isinstance(file, str):
            file_id = file
        else:
            file_id = str(file.file_id)

        if isinstance(chat_ids, str):
            chat_ids = [chat_ids]

        search_metadata = {"file_id": file_id}
        return self.memory.edit_chat_to_points(
            collection_id=collection_id,
            search_metadata=search_metadata,
            chat_ids=chat_ids,
            mode=mode
        )
    
    def add_file_to_chats(self, file, chat_ids: List[str]):
        """Add a file to a chat in the memory
        
        Args:
            file: File instance to add
            chat_id: Chat ID to add the file to
            
        Returns:
            dict: Response from the API with update status
        """

        if isinstance(file, str):
            file_id = file
        else:
            file_id = str(file.file_id)

        if isinstance(chat_ids, str):
            chat_ids = [chat_ids]

        return self.edit_file_chats(
            file_id, chat_ids, "add", "declarative"
        )
    
    def remove_file_to_chats(self, file, chat_ids: List[str]):
        """Remove a file to a chat in the memory
        
        Args:
            file: File instance to remove
            chat_id: Chat ID to remove the file to
            
        Returns:
            dict: Response from the API with update status
        """

        if isinstance(file, str):
            file_id = file
        else:
            file_id = str(file.file_id)

        if isinstance(chat_ids, str):
            chat_ids = [chat_ids]

        return self.edit_file_chats(
            file_id, chat_ids, "remove", "declarative"
        )

    def create_agent(self, agent: Union[AgentRequest, AgentComplete]):
        from agent.models import Agent

        if isinstance(agent, Agent) or isinstance(agent, AgentRequest) or  isinstance(agent, AgentComplete):
            response = self.agents.create_agent(
                data=agent.model_dump()
            )
        elif isinstance(agent, dict):
            response = self.agents.create_agent(
                data=agent
            )
        else:
            return False

        if response.get("success", False):
            return AgentComplete.model_validate(response["agent"])
        
        return None
    
    def retrieve_agent(self, agent_id: str):
        response = self.agents.retrieve_agent(agent_id=agent_id)

        if response.get("success", False):
            return AgentComplete.model_validate(response["agent"])
        
        return None
    
    def list_agents(self):
        response = self.agents.list_agents()
        return list(AgentComplete.model_validate(agent) for agent in response["agents"])
        
    def delete_agent(self, agent_id: str):
        response = self.agents.delete_agent(agent_id=agent_id)

        if response.get("success", False):
            return True
        
        return False
    
    def update_agent(self, agent: Union[AgentComplete]):
        from agent.models import Agent

        if isinstance(agent, Agent):
            response = self.agents.update_agent(agent_id=agent.agent_id, data=agent.model_dump())
        if isinstance(agent, AgentComplete):
            response = self.agents.update_agent(agent_id=agent.id, data=agent.model_dump(exclude={"id"}))
        else:
            return False

        if response.get("success", False):
            return AgentComplete.model_validate(response["agent"])
        
        return None
    
    def sync_agents(self):
        from agent.models import Agent
        """One-way: django - cat, this because cat don't know what user has created an agent"""
        
        agents = self.list_agents()
        ids = [agent.id for agent in agents]
        ids.append("default")

        queryset = Agent.objects.exclude(agent_id__in=ids)

        for agent in queryset.all():
            self.create_agent(agent)

        return queryset.count()


@wait_cat
def get_user_id(username: str):
    url = f"http://{HOST}:{PORT}/users/"
    response = requests.get(url)

    for user in response.json():
        if user["username"] == username:
            return user["id"]

    return None

def connect_as_admin() -> Cat:
    
    admin_id = get_user_id("admin")
    if (admin_id is None):
        raise ValueError("Admin user not found")
    
    config = CatConfig(user_id=admin_id, base_url=HOST, port=PORT)
    return Cat(config=config)

def connect_user(user_id) -> Cat:
    config = CatConfig(user_id=user_id, base_url=HOST, port=PORT)
    return Cat(config=config)

@wait_cat
def create_user(user):
    user_id = get_user_id(user.username)
    ic("creating user with:", user_id)

    if user_id is not None:
        user.set_manual_id(user_id)
        return True
    
    url = f"http://{HOST}:{PORT}/users/"

    payload = {
        "username": user.username,
        "permissions": {
            "CONVERSATION": ["WRITE", "EDIT", "LIST", "READ", "DELETE"],
            "MEMORY": ["READ", "LIST", "DELETE", "WRITE"],
            "STATIC": ["READ"],
            "STATUS": ["READ"]
        },
        "password": user.password
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        user.set_manual_id(response.json()["id"])
        return True
    else:
        ic(response.json())

    return False

@wait_cat
def delete_user(user):
    url = f"http://{HOST}:{PORT}/users/{user.cheshire_id}/"

    response = requests.delete(url)
    if response.status_code == 200:
        return True
    else:
        ic(response.json())

    return False