from typing import Iterable, Dict
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

from cheshire_cat.types import ChatContent, ChatToken
from groq import Groq

import cheshire_cat_api as ccat

from gtts import gTTS
from bs4 import BeautifulSoup
import markdown2

from cheshire_cat.custom_objects import CatClient


CatConfig = ccat.Config


class Cat(CatClient):
    _instances = {}  # Dizionario per memorizzare le istanze per user_id

    def __new__(cls, *args, **kwargs):
        config = kwargs.get('config')
        if not config:
            return super().__new__(cls)
        
        user_id = config.user_id
        if user_id not in cls._instances:
            wait_for_cat()
            cls._instances[user_id] = super().__new__(cls)
        return cls._instances[user_id]

    def __init__(self, *args, **kwargs):
        # Evita la reinizializzazione se l'istanza è già stata inizializzata
        if not hasattr(self, '_initialized'):
            # str is chat_id
            self._chat_queues: Dict[str, Queue] = {}
            self._message_contents: Dict[str, ChatContent] = {}
            self._stream_active: Dict[str, bool] = {}
            self.AUDIO_MAX_SIZE = 25 * 1024 * 1024  # 25MB in bytes
            
            super().__init__(on_message=self.on_message, *args, **kwargs)

            self._groq = Groq(api_key=config("GROQ_API_KEY"))

            self._initialized = True

    def connect_ws(self):
        if not self.is_ws_connected:
            return super().connect_ws()

    def startup(self):
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
        
        if msg_type == "chat":
            self._message_contents[chat_id] = ChatContent(**message)
            self.end_stream(chat_id)

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
    
    def delete_chat(self, chat_id):
        return self.memory.delete_working_memory(chat_id)
    
    def wipe_chat(self, chat_id):
        return self.memory.wipe_conversation_history_by_chat(chat_id)

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