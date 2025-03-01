from typing import List

from cat.auth.permissions import AuthPermission

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthResource


from typing import Dict, List
from pydantic import BaseModel
from fastapi import Query, Request, HTTPException, Depends
from cat.mad_hatter.decorators import endpoint
from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource

from cat.looking_glass.stray_cat import StrayCat
from cat.log import log


class MetadataUpdate(BaseModel):
    search: Dict = {}
    update: Dict = {}


# PATCH collection points metadata
@endpoint.endpoint(path="/memory/collections/{collection_id}/points/metadata", methods=["PATCH"], prefix="")
async def update_points_metadata(
    request: Request,
    metadata: MetadataUpdate,
    collection_id: str = "declarative",
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Updating points metadata for collection: {collection_id}")
    log.debug(f"Search criteria: {metadata.search}")
    log.debug(f"Update data: {metadata.update}")
    vector_memory = cat.memory.vectors
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

    log.debug(f"Updated {len(matched_points)} points in collection {collection_id}")
    return {
        "matched_points": matched_points,
        "count": len(matched_points),
        "status": result
    }

# GET points by metadata
@endpoint.get(path="/memory/collections/{collection_id}/points", prefix="")
async def get_points_by_metadata(
    request: Request,
    collection_id: str,
    metadata: Dict = {},
    cat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    """Get points in a collection by metadata filter"""
    
    vector_memory = cat.memory.vectors
    collection = vector_memory.collections.get(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=400,
            detail={"error": "Collection does not exist."}
        )

    # Construct filter from metadata
    query_filter = collection._qdrant_filter_from_dict(metadata)
    
    # Search points with the filter
    points = vector_memory.vector_db.scroll(
        collection_name=collection_id,
        scroll_filter=query_filter,
        with_payload=True,
        with_vectors=False,
        limit=10000 
    )[0]  # scroll returns (points, next_page_offset)

    if not points:
        return {
            "points": [],
            "count": 0,
            "message": "No points found matching metadata criteria"
        }

    # Extract points data
    matched_points = [{
        "id": p.id,
        "metadata": p.payload.get("metadata", {}),
    } for p in points]

    return {
        "points": matched_points,
        "count": len(matched_points)
    }

# GET points filtered by metadata
@endpoint.get(path="/memory/collections/{collection_id}/points/by_metadata", prefix="")
async def get_points_metadata_only(
    request: Request,
    collection_id: str,
    metadata: Dict = {},
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Getting points by metadata for collection: {collection_id}")
    log.debug(f"Metadata filter: {metadata}")
    vector_memory = cat.memory.vectors
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

    log.debug(f"Found {len(matched_points)} points matching metadata criteria")
    return {
        "points": matched_points,
        "count": len(matched_points)
    }

# PATCH chat_ids in memories metadata
@endpoint.endpoint(path="/memory/collections/{collection_id}/points/edit_chat_ids", methods=["PATCH"], prefix="") 
async def edit_chat_to_memories_from_metadata(
    request: Request,
    collection_id: str,
    mode: str = Query(..., description="Mode of operation: 'add' or 'remove'"),
    search_metadata: Dict = {},
    chats_id: List[str] = [],
    cat: StrayCat=Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    log.debug(f"User ID: {cat.user_id}")
    log.debug(f"Editing chat IDs in collection: {collection_id}")
    log.debug(f"Mode: {mode}, Search metadata: {search_metadata}")
    log.debug(f"Chat IDs to {mode}: {chats_id}")
    vector_memory = cat.memory.vectors
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

    log.debug(f"Updated {len(points)} points with new chat IDs")
    return {
        "matched_points": len(points),
        "updated_metadata": current_metadata,
        "status": result
    }
