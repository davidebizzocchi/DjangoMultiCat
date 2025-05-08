from typing import Optional, Dict
from pydantic import BaseModel
from fastapi import Request, HTTPException, Depends

from cat.auth.permissions import AuthPermission, AuthResource
from cat.auth.connection import HTTPAuth
from cat.mad_hatter.decorators import endpoint
from cat.looking_glass.stray_cat import StrayCat
from cat.factory.llm import get_llms_schemas


class LLMRequest(BaseModel):
    name: str
    llm_class: str
    config: dict

class LLMUpdateRequest(BaseModel):
    name: Optional[str] = None
    llm_class: Optional[str] = None 
    config: Optional[dict] = None


@endpoint.get(path="/llms", prefix="")
async def list_llm(
    request: Request,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.READ)),
) -> Dict:
    """List all available llms"""
    return {
        "llms": list(cat.llms(cast=False))
    }

@endpoint.get(path="/llms/schema", prefix="")
async def llms_schema(
    request: Request,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.READ)),
) -> Dict:
    """Get available LLM schemas"""
    return {
        "schemas": get_llms_schemas(),
        "return_type": LLMRequest.model_json_schema()
    }

@endpoint.get(path="/llms/{llm_name}", prefix="")
async def retrieve_llm(
    request: Request,
    llm_name: str,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.READ)),
) -> Dict:
    """Get information about a specific LLM"""
    llm = cat.get_llm_by_name(llm_name)
    
    if llm is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "LLM not found"}
        )
    
    return {
        "llm": llm
    }

@endpoint.post(path="/llms", prefix="")
async def create_llm(
    request: Request,
    data: LLMRequest,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)),
) -> Dict:
    """Create a new LLM"""
    new_llm = cat.create_llm(
        name=data.name,
        llm_class=data.llm_class,
        config=data.config
    )
    
    return {
        "success": True,
        "llm": new_llm
    }

@endpoint.endpoint(path="/llms", prefix="", methods=["PATCH"])
async def update_llm(
    request: Request,
    data: LLMUpdateRequest,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)),
) -> Dict:
    """Update an existing LLM"""
    llm = cat.get_llm_by_name(data.name)

    if llm is None:
        return {
            "success": True,
            "llm": cat.create_llm(
                name=data.name,
                llm_class=data.llm_class,
                config=data.config
            )
        }

    if data.name is not None:
        llm.name = data.name
    if data.llm_class is not None:
        llm.llm_class = data.llm_class
    if data.config is not None:
        llm.config = data.config

    updated_llm = cat.update_llm(llm)

    return {
        "success": True,
        "llm": updated_llm
    }

@endpoint.endpoint(path="/llms/{llm_name}", prefix="", methods=["DELETE"])
async def delete_llm(
    request: Request,
    llm_name: str,
    cat: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)),
) -> Dict:
    """Delete an existing LLM"""
    llm = cat.get_llm_by_name(llm_name)
    
    if llm is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "LLM not found"}
        )

    cat.delete_llm(llm_name)
    
    return {
        "success": True,
        "message": f"LLM {llm_name} deleted successfully"
    }
