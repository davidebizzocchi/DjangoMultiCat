import cheshire_cat_api as ccat
from icecream import ic
# from users.models import UserProfile
import requests
import time
from functools import wraps
from cheshire_cat.decorators import wait_cat, HOST, PORT
import json
from queue import Queue

from cheshire_cat.types import ChatContent, ChatToken

CatConfig = ccat.Config



class Cat(ccat.CatClient):

    def __init__(self, *args, **kwargs):
        self._chat_token_queue = Queue()
        self._message_content = None
        self._stream_active = False
        super().__init__(on_message=self.on_message, *args, **kwargs)

    def send(self, *args, **kwargs):
        """Send prompt to ws"""
        self._reset_new_message()

        return super().send(*args, **kwargs)

    def on_message(self, message):
        """Callback for message received"""
        ic(message)

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

    def stream(self):
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
    
@wait_cat
def get_user_id(username: str):
    url = f"http://{HOST}:{PORT}/users/"
    response = requests.get(url)

    for user in response.json():
        if user["username"] == username:
            return user["id"]

    return None

@wait_cat
def connect_as_admin() -> Cat:
    
    admin_id = get_user_id("admin")
    if admin_id is None:
        raise ValueError("Admin user not found")
    
    config = CatConfig(user_id=admin_id, base_url=HOST, port=PORT)
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