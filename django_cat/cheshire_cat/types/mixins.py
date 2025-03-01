# Mixins for add attributes to models

from typing import Optional


class ChatIDMixin:
    """
    Mixin class to add chat
    Attributes
    ----------
    chat_id : str
        The ID of the chat.
    """

    chat_id: Optional[str] = "default"