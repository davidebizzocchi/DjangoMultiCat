from typing import Any, Callable, Type, Union
from .utils import set_redirect_class
from cat.log import log

def get_true_class(cls):
    """
    Returns the true class of an object, even if it has been decorated or modified.
    """
    if hasattr(cls, "__closure__"):
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

    true_old_class = get_true_class(old_class)

    def _make_with_name() -> Callable:

        print("true_old_class:", true_old_class.__name__)
        def _make_option(class_: Type[Any]) -> Type:
            true_class_ = get_true_class(class_)
            print("class:", true_class_.__name__)
            # Imposta sempre il redirect usando l'utility function
            set_redirect_class(true_old_class, true_class_)
            return true_class_
            
        return _make_option
    
    print("old_class:", true_old_class.__name__)
    try:
        true_old_class.__name__
    except AttributeError:
        log.error(f"old_class must be a class, got {old_class}")
        raise ValueError("old_class must be a class")

    return _make_with_name()