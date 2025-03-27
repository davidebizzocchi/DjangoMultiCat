from cat.plugins.multicat.cache.base import BaseStrayCache


class FatherSonCache(BaseStrayCache):
    def __init__(self, max_items=4, precision=1, protected_keys=["default"]):
        super().__init__(
            max_items=max_items,
            precision=precision,
            protected_keys=protected_keys
        )
