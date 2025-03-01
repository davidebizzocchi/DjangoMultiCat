from cat.auth.permissions import AuthPermission

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthResource

from typing import Dict
from fastapi import Request, HTTPException, Depends
from cat.mad_hatter.decorators import endpoint
from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource

from cat.looking_glass.stray_cat import StrayCat
from cat.log import log


# GET lista delle working memories 
@endpoint.get(path="/memory/working_memories", prefix="")
async def get_working_memories_list(
    request: Request,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Getting list of working memories")
    result = {"working_memories": list(cat.chat_list)}
    log.debug(f"Found {len(result['working_memories'])} working memories")
    return result

# GET una specifica working memory
@endpoint.get(path="/memory/working_memories/{chat_id}", prefix="")
async def get_working_memory(
    request: Request,
    chat_id: str, 
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Getting working memory for chat_id: {chat_id}")
    if chat_id not in cat.chat_list:
        log.debug(f"Working memory {chat_id} not found")
        raise HTTPException(
            status_code=404,
            detail={"error": f"Working memory {chat_id} does not exist."}
        )
    result = {"history": cat.get_son(chat_id).history}
    log.debug(f"Returned history with {len(result['history'])} messages for chat_id: {chat_id}")
    return result

# DELETE una working memory
@endpoint.endpoint(path="/memory/working_memories/{chat_id}", methods=["DELETE"], prefix="")
async def delete_working_memory(
    request: Request,
    chat_id: str,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.DELETE)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Attempting to delete working memory for chat_id: {chat_id}")
    if chat_id not in cat.chat_list:
        log.debug(f"Working memory {chat_id} not found for deletion")
        return {
            "deleted": False,
            "message": "There is no working memory"
        }
    stray_son = cat.get_son(chat_id)
    del stray_son
    log.debug(f"Successfully deleted working memory for chat_id: {chat_id}")
    return {
        "deleted": True,
        "chat_id": chat_id
    }
