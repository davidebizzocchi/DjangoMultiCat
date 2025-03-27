from cat.cache.in_memory_cache import InMemoryCache


class BaseStrayCache(InMemoryCache):
    def __init__(self, max_items=100, precision=0.1, protected_keys=[]):
        super().__init__()

        self.max_items = max_items
        self.precision = precision

        self.protected_keys = protected_keys

    def insert(self, cache_item):
        """Insert a key-value pair in the cache.

        Parameters
        ----------
        cache_item : CacheItem
            Cache item to store.

        """

        # add new item
        self.items[cache_item.key] = cache_item
        
        # clean up cache if it's full
        len_items = len(self.items)
        if len_items >= self.max_items:

            # sort caches by creation time
            sorted_items = sorted(
                self.items.items(),
                key=lambda x: x[1].created_at,
            )

            # delete "precision" of the oldest items
            # not efficient, but it's honest work
            # TODO: index items also by creation date            
            for k, v in sorted_items[:int((len_items - self.max_items)*self.precision + self.max_items*(1 - self.precision)) + len(self.protected_keys)]:
                self.delete(k)

    def delete(self, key):
        if key in self.protected_keys:
            return

        super().delete(key)

