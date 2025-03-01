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
