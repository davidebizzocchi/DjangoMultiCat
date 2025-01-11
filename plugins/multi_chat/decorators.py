from typing import Any, Callable, Type, Union
from cat.log import log
from cat import utils

def get_true_class(cls):
    if type(cls) == type(lambda: None):
        return cls.__closure__[0].cell_contents
    return cls


def option(old_class: Type, *args: Union[str, Type[Any]], priority: int = 1) -> Callable:
    """
    Make options out of classes, can be used with or without arguments.
    old_class: The class to be replaced
    
    Examples:
        .. code-block:: python
            @option(OldClass)
            class MyOption:
                pass
            
            @option(OldClass, priority=2)
            class MyOption:
                pass
    """

    old_class = get_true_class(old_class)

    def _make_with_name() -> Callable:
        option_name = old_class.__name__
        log.error(f"option name {option_name}")
        def _make_option(class_):
            log.error(f"option class {class_}")
            class_ = get_true_class(class_)

            log.error(f"make option {option_name}")
            add_redirect_logic(old_class)
            log.error(f"add redirect logic {option_name}")
            set_redirect_class(old_class, class_)
            log.error(f"set redirect class {option_name}")
            return class_
        return _make_option
    
    log.error(f"option {old_class.__name__}")
    try:
        old_class.__name__
    except AttributeError:
        raise ValueError("old_class must be a class")

    return _make_with_name()

def add_redirect_logic(cls):
    """
    Aggiunge la logica di redirezione a una classe esistente.
    Modifica dinamicamente il comportamento di __new__.
    """
    if hasattr(cls, "_redirect_class"):
        log.debug(f"Redirect logic already added to {cls.__name__}")
        return

    # Aggiungi l'attributo per la classe di redirezione
    cls._redirect_class = None

    # Salva il vecchio __new__ per preservare il comportamento originale
    original_new = cls.__new__

    def new_with_redirect(cls, *args, **kwargs):
        # Reindirizza se _redirect_class è impostata
        if cls._redirect_class:
            if cls.__name__ != cls._redirect_class.__name__:
                log.info(f"Redirecting {cls.__name__} to {cls._redirect_class.__name__}")
                return cls._redirect_class.__new__(cls._redirect_class)
            
            # return cls._redirect_class
        return original_new(cls)

    # Sostituisci __new__ con la nuova logica
    cls.__new__ = classmethod(new_with_redirect)

    # Aggiungi un metodo per impostare la classe di redirezione
    @classmethod
    def set_redirect(cls, redirect_class):
        cls._redirect_class = redirect_class
        log.info(f"{cls.__name__} is now redirected to {redirect_class.__name__}")

    cls.set_redirect = set_redirect

def set_redirect_class(original_class, redirected_class):
    """
    Set a class redirection for the original class to the redirected class.
    
    Args:
        original_class (type): The class that will be redirected.
        redirected_class (type): The class to redirect to.
    """
    # Handle singleton decorated classes
    if hasattr(original_class, 'original_class'):
        target_class = original_class.original_class
    else:
        target_class = original_class

    # The class is using metaclass=redirect_meta
    if hasattr(target_class, "_redirect_to"):
        target_class._redirect_to[target_class] = redirected_class
    else:
        add_redirect_logic(target_class)
        target_class.set_redirect(redirected_class)