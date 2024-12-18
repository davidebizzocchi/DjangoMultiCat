import mimetypes
from typing import Iterable, Dict, List
from icecream import ic
# from users.models import UserProfile
import requests
import time
from functools import wraps
from cheshire_cat.decorators import wait_cat, HOST, PORT, wait_for_cat
import json
from queue import Queue
from decouple import config
import io
from collections import deque
from typing import NamedTuple, Deque
import uuid

from cheshire_cat.types import ChatContent, ChatHistoryMessage, ChatToken, ChatHistory, GenericMessage, Notification
from groq import Groq

import cheshire_cat_api as ccat

from gtts import gTTS
from bs4 import BeautifulSoup
import markdown2

from cheshire_cat.custom_objects import CatClient


CatConfig = ccat.Config

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
            instance._initialized = False  # Flag per evitare reinizializzazione
            cls._instances[user_id] = instance
        return cls._instances[user_id]

    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_initialized') or not self._initialized:
            # str is chat_id
            self._chat_queues: Dict[str, Queue] = {}
            self._message_contents: Dict[str, ChatContent] = {}
            self._stream_active: Dict[str, bool] = {}
            self.AUDIO_MAX_SIZE = 25 * 1024 * 1024  # 25MB in bytes
            
            super().__init__(on_message=self.on_message, *args, **kwargs)

            self._groq = Groq(api_key=config("GROQ_API_KEY"))
            self.startup()
            
            self._notification_handlers: Dict[str, callable] = {}
            self._notifications: Deque[Notification] = deque()
            self._notification_ttl = 60  # 1 minuto in secondi
            self._initialized = True

    def _check_ws_connection(self):
        if not self.is_ws_connected:
            self.startup()

    def connect_ws(self):
        if not self.is_ws_connected:
            return super().connect_ws()

    def startup(self):
        ic(self.is_ws_connected)
        if self.is_ws_connected:
            return self
        
        self.connect_ws()

        counter = 0
        while not self.is_ws_connected:
            time.sleep(0.2)
            counter += 1

            if counter == 100:
                raise TimeoutError("Cannot connect to the websocket")

        return self

    def send(self, message, chat_id="default", *args, **kwargs):
        """Send prompt to ws with specific chat_id"""
        self._reset_new_message(chat_id)
        self._check_ws_connection()
        return super().send(message, chat_id=chat_id, *args, **kwargs)

    def on_message(self, message):
        """Callback for message received"""
        # ic(message)

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
            chat_message = ChatToken(**message)
            
            if chat_id in self._stream_active:
                self._chat_queues[chat_id].put(chat_message)
        
        elif msg_type == "chat":
            self._message_contents[chat_id] = ChatContent(**message)
            self.end_stream(chat_id)
        
        elif msg_type == "notification":
            notification = Notification(**message)
            self._add_notification(notification)
            # Chiamare tutti gli handler registrati
            for handler in self._notification_handlers.values():
                handler(notification)
        
        else:
            # Handle generic messages
            generic_message = GenericMessage(**message)
            # You can add specific handling for other message types here
            ic(f"Received generic message: {generic_message}")

    def end_stream(self, chat_id: str = "default"):
        """End stream for specific chat"""
        if chat_id in self._stream_active:
            self._stream_active[chat_id] = False
            self._chat_queues[chat_id].put(None)

    def _stream(self, chat_id):
        """Stream messages for specific chat"""

        while self._stream_active.get(chat_id):
            try:
                token = self._chat_queues[chat_id].get(block=True)
                if token is None:  # segnale di terminazione
                    break
                yield token
            except Queue.Empty:
                continue  # Continuiamo ad ascoltare se la coda è vuota
            except Exception as e:
                ic(f"Stream error for chat {chat_id}: {e}")
                break

    def stream(self, chat_id: str = "default") -> Iterable[ChatToken]:
        """Stream messages for specific chat"""

        if chat_id not in self._stream_active:
            yield f"Error: {chat_id} this chat is not active"
            return
        
        # Modifica qui: yield from invece di una semplice chiamata
        yield from self._stream(chat_id)

    def get_message_content(self, chat_id: str = "default") -> ChatContent:
        return self._message_contents.get(chat_id)
    
    def wait_message_content(self, chat_id: str = "default") -> ChatContent:
        while self._message_contents.get(chat_id) is None:
            time.sleep(0.1)
        return self._message_contents[chat_id]
    
    def _transcribe(self, audio_bytes):
        start = time.time()
        transcription = self._groq.audio.transcriptions.create(
            file=("temp.wav", audio_bytes),
            model="whisper-large-v3",
            language="it",
            prompt="Trascrivi il messaggio dell'utente",
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
    
    def _speak(self, text):
        tts = gTTS(
            text=self.parse_markdown(text),
            lang="it",
        )

        stream = io.BytesIO()
        tts.write_to_fp(stream)

        stream.seek(0)

        return stream
    
    def speak(self, text):
        return self._speak(text)
    
    def get_collections_name(self, name: str) -> Iterable[str]:
        for collection in self.memory.get_collections()["collections"]:
            yield collection["name"]

    def delete_chat(self, chat_id):
        self.memory.wipe_memory_points_by_metadata(
            collection_id="episodic",
            body={"chat_id": chat_id}
        )
        return self.memory.delete_working_memory(chat_id)
    
    def wipe_chat(self, chat_id):
        return self.memory.wipe_conversation_history_by_chat(chat_id)
    
    def get_chat_history(self, chat_id):
        response = self.memory.get_working_memory(chat_id)
        if "history" in response:
            return ChatHistory(messages=[
                ChatHistoryMessage(**msg) for msg in response["history"]
            ])
        return ChatHistory()

    def get_chat_list(self):
        return self.memory.get_working_memories_list()

    def register_notification_handler(self, handler) -> str:
        """
        Registra un handler per le notifiche e restituisce il suo ID
        
        Args:
            handler: Funzione che riceve una notifica
            
        Returns:
            str: ID univoco dell'handler registrato
        """
        handler_id = str(uuid.uuid4())
        self._notification_handlers[handler_id] = handler
        return handler_id

    def unregister_notification_handler(self, handler_id: str):
        """
        Rimuove un handler dato il suo ID
        
        Args:
            handler_id: ID dell'handler da rimuovere
        """
        if handler_id in self._notification_handlers:
            del self._notification_handlers[handler_id]

    def unregister_all_notification_handlers(self):
        """Rimuove tutti gli handler registrati"""
        self._notification_handlers.clear()

    def _cleanup_old_notifications(self):
        """Rimuove le notifiche più vecchie di TTL secondi"""
        current_time = time.time()
        while self._notifications and (current_time - self._notifications[0].received_at) > self._notification_ttl:
            self._notifications.popleft()

    def _add_notification(self, notification: Notification):
        """Aggiunge una nuova notifica e pulisce quelle vecchie"""
        self._cleanup_old_notifications()
        self._notifications.append(notification)

    def get_recent_notifications(self):
        """Restituisce le notifiche recenti dopo aver pulito quelle vecchie"""
        self._cleanup_old_notifications()
        return list(self._notifications)
    
    def upload_file(self, file, metadata: Dict, chunk_size=None, chunk_overlap=None):
        url =  f"http://{HOST}:{PORT}/rabbithole/"
        files = {"file": (
            str(file.file_id),
            open(file.file.path.absolute(), "rb"),
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
            data=payload
        ).json()
    
    def delete_file(self, file):
        return self.memory.wipe_memory_points_by_metadata(
            collection_id="declarative",
            body={
                "file_id": str(file.file_id)
            }
        )

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
    if admin_id is None:
        raise ValueError("Admin user not found")
    
    config = CatConfig(user_id=admin_id, base_url=HOST, port=PORT)
    return Cat(config=config)

def connect_user(user_id) -> Cat:
    config = CatConfig(user_id=user_id, base_url=HOST, port=PORT)
    return Cat(config=config)

@wait_cat
def create_user(user):
    ic(get_user_id(user.username))
    if get_user_id(user.username) is not None:
        return True
    
    url = f"http://{HOST}:{PORT}/users/"

    payload = {
        "username": user.username,
        "permissions": {
            "CONVERSATION": ["WRITE", "EDIT", "LIST", "READ", "DELETE"],
            "MEMORY": ["READ", "LIST"],
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
    url = f"http://{HOST}:{PORT}/users/{user.cheschire_id}/"

    response = requests.delete(url)
    if response.status_code == 200:
        return True
    else:
        ic(response.json())

    return False