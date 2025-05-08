from typing import Optional

from cat.plugins.multicat.decorators import option
from cat.convo.messages import CatMessage


@option(CatMessage)
class CatMessageChat(CatMessage):
    chat_id: Optional[str] = "default"