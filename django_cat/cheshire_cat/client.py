import cheshire_cat_api as ccat
from icecream import ic
import cheshire_cat_api.config as CatConfig


class Cat(ccat.CatClient):

    def on_message(self, message):
        ic(message)