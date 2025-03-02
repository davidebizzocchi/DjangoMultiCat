from typing import Optional

from cat.plugins.multicat.decorators import option
from cat.convo.messages import UserMessage


@option(UserMessage)
class UserMessageChat(UserMessage):
    """Message class with chat and agent identification"""

    chat_id: Optional[str] = "default"
    agent_id: Optional[str] = "default"
