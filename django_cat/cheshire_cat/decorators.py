from functools import wraps
import requests
import time
from decouple import config

HOST = config("CAT_HOST", default="cheshire-cat-core")
PORT = config("CAT_PORT", default=80)

def wait_for_cat():
    url = f"http://{HOST}:{PORT}"

    while True:
        time.sleep(1)

        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            continue

        if response.status_code == 200:
            break

    return True

def wait_cat(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wait_for_cat()
        return func(*args, **kwargs)
    return wrapper