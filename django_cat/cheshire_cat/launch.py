from icecream import ic
import time
import cheshire_cat_api as ccat
import requests
from django.dispatch import receiver
from app.signals import server_start

from cheshire_cat.client import Cat, CatConfig

cat_client: Cat = None

def main():
    ic("ciao")
    global cat_client

    response, user_id = None, None
    while True:
        time.sleep(1)

        url = "http://cheshire-cat-core:80/users/"
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

    
    # if user_id is not None:

    if user_id is not None:
        config = CatConfig(user_id=user_id, base_url="cheshire-cat-core", port=80)
        cat_client = Cat(
            config=config
        )

        cat_client.connect_ws()
        ic("connect")

        while not cat_client.is_ws_connected: 
        # A better handling is strongly advised to avoid an infinite loop 
            time.sleep(1)

        ic("CONNESS")


@receiver(server_start)
def start_cheshire_cat(sender=None, **kwargs):
    if cat_client is not None:
        cat_client.close()
        ic("disconnect")

    # main()
