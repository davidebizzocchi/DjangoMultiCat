from cat.log import log


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
                log.debug(f"Redirecting {cls.__name__} to {cls._redirect_class.__name__}")
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

    # The class is using metaclass=redirect_meta
    if hasattr(original_class, "_redirect_to"):
        original_class._redirect_to[original_class] = redirected_class

    # The class is not using metaclass=redirect_meta, so force redirection
    else:
        add_redirect_logic(original_class)
        original_class.set_redirect(redirected_class)