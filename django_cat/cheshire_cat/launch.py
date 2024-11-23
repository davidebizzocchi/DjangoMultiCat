from icecream import ic
from time import sleep
import cheshire_cat_api as ccat
import requests

def main():
    ic("ciao")
    response, user_id = None
    while True:
        sleep(1)

        url = "http://localhost:1865/users/"
        response = requests.get(url)

        ic(response.status_code)
        if response.status_code == 200:
            break
    
    if response is not None:
        data = response.json()

        for user in data:
            if user["username"] == "admin":
                user_id = user["id"]
                ic(user_id)
                break

    
    if user_id is not None:
        config = ccat.Config(user_id=user_id)