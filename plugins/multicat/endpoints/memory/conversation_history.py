import pprint
from cat.auth.permissions import AuthPermission

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthResource

from typing import Dict
from fastapi import Request, Depends
from cat.mad_hatter.decorators import endpoint
from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource

from cat.looking_glass.stray_cat import StrayCat
from cat.log import log

from cat.convo.messages import UserMessage, CatMessage


# GET conversation history from working memory
@endpoint.get(path="/memory/conversation_history", prefix="")
async def get_conversation_history(
    request: Request,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Getting conversation history")
    result = {"history": cat.working_memory.history}
    log.debug(f"Returned history with {len(result['history'])} messages")
    return result

# DELETE vector memory by chat_id
@endpoint.endpoint(path="/memory/conversation_history/{chat_id}", methods=["DELETE"], prefix="")
async def wipe_vector_memory_by_chat(
    request: Request,
    chat_id: str,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.DELETE)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Wiping vector memory for chat_id: {chat_id}")
    
    if chat_id in cat.chat_list:
        cat.get_son(chat_id).history = []
        log.debug(f"Successfully wiped history for chat_id: {chat_id}")
    
    return {
        "deleted": True,
        "chat_id": chat_id
    }

# POST add message(s) to conversation history
@endpoint.post(path="/memory/conversation_history/{chat_id}", prefix="")
async def add_message_to_conversation_history(
    request: Request,
    chat_id: str,
    data: Dict,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    message = data.get("message", {})
    index = data.get("index", 0)

    if message.get("who", None) == "Human":
        message = UserMessage.model_validate(message)
    elif message.get("who", None) == "AI":
        message = CatMessage.model_validate(message)
    else:
        return {
            "success": False,
            "error": "Invalid message type"
        }

    log.debug(f"Adding message to conversation history for chat_id: {chat_id}")
    log.debug(f"Message: {pprint.pformat(message)}, Index: {index}")
        
    # SonStrayCat
    chat_cat = cat.get_son(chat_id)

    # This let specify a negative index, for make an append
    # So if index is -1, the message will be appended at the end
    if index < 0:
        index = len(chat_cat.history) + index + 1

    # Check that the index is not out of bounds
    if index > len(chat_cat.history):
        index = len(chat_cat.history)

    # Insert the message at the specified index
    chat_cat.history.insert(index, message)

    return {
        "success": True,
        "chat_id": chat_id,
    }

# Get the legnth of the conversation history
@endpoint.get(path="/memory/conversation_history/{chat_id}/length", prefix="")
async def get_conversation_history_length(
    request: Request,
    chat_id: str,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:

    return {
        "length": len(cat.get_son(chat_id).history),
        "chat_id": chat_id
    }