class SingletonMeta(type):
    """A metaclass to implement the Singleton pattern."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # If instance doesn't exist, create and store it
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
    
class BaseSingleton(metaclass=SingletonMeta):
    pass

class SubClassA(BaseSingleton):
    pass

class SubClassB(BaseSingleton):
    pass


# All three classes are singletons,
# although they DO NOT share the same instance, but different ones