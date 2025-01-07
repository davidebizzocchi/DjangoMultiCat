from typing import Callable, List

from cat.auth.permissions import AuthPermission

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthResource


from typing import Dict, List
from pydantic import BaseModel
from fastapi import Query, Request, HTTPException, Depends
from cat.mad_hatter.decorators import endpoint
from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource

# from plugins.multi_chat.refactory import FatherStrayCat
from cat.looking_glass.stray_cat import StrayCat

# StrayCat = FatherStrayCat

class MetadataUpdate(BaseModel):
    search: Dict = {}
    update: Dict = {}

# GET conversation history from working memory
@endpoint.get("/memory/conversation_history")
async def get_conversation_history(
    request: Request,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    return {"history": stray.working_memory.history}

# GET lista delle working memories 
@endpoint.get("/memory/working_memories")
async def get_working_memories_list(
    request: Request,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    return {"working_memories": list(stray.chat_list)}

# GET una specifica working memory
@endpoint.get("/memory/working_memories/{chat_id}")
async def get_working_memory(
    request: Request,
    chat_id: str, 
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    if chat_id not in stray.chat_list:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Working memory {chat_id} does not exist."}
        )
    return {"history": stray.get_son(chat_id).history}

# DELETE una working memory
@endpoint.endpoint(path="/memory/working_memories/{chat_id}", methods=["DELETE"])
async def delete_working_memory(
    request: Request,
    chat_id: str,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.DELETE)),
) -> Dict:
    if chat_id not in stray.chat_list:
        return {
            "deleted": False,
            "message": "There is no working memory"
        }
    stray_son = stray.get_son(chat_id)
    del stray_son
    return {
        "deleted": True,
        "chat_id": chat_id
    }

# PATCH collection points metadata
@endpoint.endpoint(path="/memory/collections/{collection_id}/points/metadata", methods=["PATCH"])
async def update_points_metadata(
    request: Request,
    metadata: MetadataUpdate,
    collection_id: str = "declarative",
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    vector_memory = stray.memory.vectors
    collection = vector_memory.collections.get(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=400,
            detail={"error": "Collection does not exist."}
        )

    query_filter = collection._qdrant_filter_from_dict(metadata.search)
    points = vector_memory.vector_db.scroll(
        collection_name=collection_id,
        scroll_filter=query_filter,
        with_payload=True,
        with_vectors=False,
        limit=10000 
    )[0]

    if not points:
        return {
            "matched_points": [],
            "message": "No points found matching search criteria"
        }

    matched_points = []
    for p in points:
        current_metadata: Dict = p.payload.get("metadata", {}).copy()
        current_metadata.update(metadata.update)
        matched_points.append({
            "id": p.id,
            "metadata": current_metadata
        })

    result = collection.update_points_by_metadata(
        points_ids=[p["id"] for p in matched_points],
        metadata={"metadata": matched_points[0]["metadata"]}
    )

    return {
        "matched_points": matched_points,
        "count": len(matched_points),
        "status": result
    }

# GET points filtered by metadata
@endpoint.get("/memory/collections/{collection_id}/points/by_metadata")
async def get_points_metadata_only(
    request: Request,
    collection_id: str,
    metadata: Dict = {},
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    vector_memory = stray.memory.vectors
    collection = vector_memory.collections.get(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=400,
            detail={"error": "Collection does not exist."}
        )

    query_filter = collection._qdrant_filter_from_dict(metadata)
    points = vector_memory.vector_db.scroll(
        collection_name=collection_id,
        scroll_filter=query_filter,
        with_payload=True,
        with_vectors=False,
        limit=10000 
    )[0]

    if not points:
        return {
            "points": [],
            "count": 0,
            "message": "No points found matching metadata criteria"
        }

    matched_points = [{
        "id": p.id,
        "metadata": p.payload.get("metadata", {}),
    } for p in points]

    return {
        "points": matched_points,
        "count": len(matched_points)
    }

# PATCH chat_ids in memories metadata
@endpoint.endpoint(path="/memory/collections/{collection_id}/points/edit_chat_ids", methods=["PATCH"]) 
async def edit_chat_to_memories_from_metadata(
    request: Request,
    collection_id: str,
    mode: str = Query(..., description="Mode of operation: 'add' or 'remove'"),
    search_metadata: Dict = {},
    chats_id: List[str] = [],
    stray: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    vector_memory = stray.memory.vectors
    collection = vector_memory.collections.get(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=400,
            detail={"error": "Collection does not exist."}
        )

    query_filter = collection._qdrant_filter_from_dict(search_metadata)
    points = vector_memory.vector_db.scroll(
        collection_name=collection_id,
        scroll_filter=query_filter,
        with_payload=True,
        with_vectors=False,
        limit=10000 
    )[0]

    if not points:
        return {
            "matched_points": [],
            "message": "No points found matching search criteria"
        }

    first_point = points[0]
    current_metadata = first_point.payload.get("metadata", {}).copy()
    
    if "chats_id" not in current_metadata:
        current_metadata["chats_id"] = []

    if mode == "add":
        current_metadata["chats_id"] = list(set(current_metadata["chats_id"] + chats_id))
    elif mode == "remove":
        current_metadata["chats_id"] = [chat_id for chat_id in current_metadata["chats_id"] if chat_id not in chats_id]
    else:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid mode specified, use 'add' or 'remove'"}
        )
    
    result = collection.update_points_by_metadata(
        points_ids=[p.id for p in points],
        metadata={"metadata": current_metadata}
    )

    return {
        "matched_points": len(points),
        "updated_metadata": current_metadata,
        "status": result
    }
