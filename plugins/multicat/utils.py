from cat.log import log


def add_redirect_logic(cls):
    """
    Adds redirection logic to an existing class.
    Dynamically modifies __new__ behavior.
    """
    if hasattr(cls, "_redirect_class"):
        log.debug(f"Redirect logic already added to {cls.__name__}")
        return

    # Add attribute for redirection class
    cls._redirect_class = None

    # Save old __new__ to preserve original behavior
    original_new = cls.__new__

    def new_with_redirect(cls, *args, **kwargs):
        # Redirect if _redirect_class is set
        if cls._redirect_class:
            if cls.__name__ != cls._redirect_class.__name__:
                log.debug(f"Redirecting {cls.__name__} to {cls._redirect_class.__name__}")
                return cls._redirect_class.__new__(cls._redirect_class)
            
            # return cls._redirect_class
        return original_new(cls)

    # Replace __new__ with new logic
    cls.__new__ = classmethod(new_with_redirect)

    # Add method to set redirection class
    @classmethod
    def set_redirect(cls, redirect_class):
        cls._redirect_class = redirect_class
        log.info(f"{cls.__name__} is now redirected to {redirect_class.__name__}")

    cls.set_redirect = set_redirect

def set_redirect_class(original_class, redirected_class):
    """
    Set a class redirection from the original class to the redirected class.
    
    Args:
        original_class (type): The class that will be redirected.
        redirected_class (type): The class to redirect to.
    """

    # The class is using metaclass=redirect_meta
    if hasattr(original_class, "_redirect_to"):
        original_class._redirect_to[original_class] = redirected_class

    # The class is not using metaclass=redirect_meta, so force redirection
    else:
        add_redirect_logic(original_class)
        original_class.set_redirect(redirected_class)