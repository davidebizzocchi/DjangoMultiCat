from cat.plugins.multicat.cache.base import BaseStrayCache


class UserFatherCache(BaseStrayCache):
    def __init__(self, max_items=100, precision=0.2, protected_keys=["user"]):
        super().__init__(
            max_items=max_items,
            precision=precision,
            protected_keys=protected_keys
        )
