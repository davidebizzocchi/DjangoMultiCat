from typing import Iterable
import cheshire_cat_api as ccat
from icecream import ic
# from users.models import UserProfile
import requests
import time
from functools import wraps
from cheshire_cat.decorators import wait_cat, HOST, PORT, wait_for_cat
import json
from queue import Queue
from decouple import config

from cheshire_cat.types import ChatContent, ChatToken
from groq import Groq


CatConfig = ccat.Config


class Cat(ccat.CatClient):
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
            self._chat_token_queue = Queue()
            self._message_content = None
            self._stream_active = False

            super().__init__(on_message=self.on_message, *args, **kwargs)

            self._groq = Groq(api_key=config("GROQ_API_KEY"))

            self._initialized = True

    def startup(self):
        self.connect_ws()

        counter = 0
        while not self.is_ws_connected:
            time.sleep(0.2)
            counter += 1

            if counter == 100:
                raise TimeoutError("Cannot connect to the websocket")

        return self

    def send(self, message, *args, **kwargs):
        """Send prompt to ws"""
        self._reset_new_message()

        return super().send(message, *args, **kwargs)

    def on_message(self, message):
        """Callback for message received"""
        # ic(message)

        msg_json = json.loads(message)
        self._on_message(msg_json)

    def _reset_new_message(self):
        self._chat_token_queue = Queue()
        self._message_content = None
        self._stream_active = True

    def _on_message(self, message: dict):
        """Handle for messages"""
        msg_type = message.get("type", None)

        if msg_type == "chat_token":
            chat_message = ChatToken(**message)
            self._chat_token_queue.put(chat_message)
        
        if msg_type == "chat":
            self._message_content = ChatContent(**message)
            self.end_stream()

    def end_stream(self):
        """Termina lo stream mettendo un None nella coda"""
        self._stream_active = False
        self._chat_token_queue.put(None)

    def stream(self) -> Iterable[ChatToken]:
        """
        Generator that yields ChatToken objects as they arrive
        """
        self._stream_active = True
        while self._stream_active:
            try:
                token = self._chat_token_queue.get(block=True)
                if token is None:  # segnale di terminazione
                    break
                
                yield token
            except Exception as e:
                ic(f"Stream error: {e}")
                break

    def get_message_content(self) -> ChatContent:
        return self._message_content
    
    def wait_message_content(self) -> ChatContent:
        while self._message_content is None:
            time.sleep(0.1)
        return self._message_content
    
    def transcribe(self, audio_bytes):
        start = time.time()

        audio_bytes.seek(0)
        transcription = self._groq.audio.transcriptions.create(
            file=("temp.wav", audio_bytes.read()),
            model="whisper-large-v3",
            language="it",
            prompt="Trascrivi il messaggio dell'utente",
            response_format="json"
        )

        ic("time", time.time() - start, transcription)
        return transcription.text.strip()
    
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