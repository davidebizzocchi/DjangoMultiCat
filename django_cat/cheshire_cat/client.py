import cheshire_cat_api as ccat
from icecream import ic
import cheshire_cat_api.config as CatConfig
from users.models import UserProfile
import requests

HOST = "cheshire-cat-core"
PORT = 80

class Cat(ccat.CatClient):

    def __init__(self, *args, **kwargs):
        super().__init__(on_message=self.on_message, *args, **kwargs)

    def on_message(self, message):
        ic(message)

def connect_as_admin() -> Cat:
    url = "http://{HOST}:{PORT}/users/"
    response = requests.get(url)

    for user in response.json():
        if user["username"] == "admin":
            user_id = user["id"]
            break
    
    config = CatConfig(user_id=user_id, base_url="cheshire-cat-core", port=80)
    return Cat(config=config)

def create_user(user: UserProfile):
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
        user.user_id = response.json()["id"]
        user.save()
        return True
    else:
        ic(response.json())

    return False


def delete_user(user: UserProfile):
    url = f"http://{HOST}:{PORT}/users/{user.user_id}/"

    response = requests.delete(url)
    if response.status_code == 200:
        return True
    else:
        ic(response.json())

    return False