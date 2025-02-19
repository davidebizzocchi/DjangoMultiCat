from typing import List, Optional

from cat.auth.permissions import AuthPermission

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthResource


from typing import Dict, List
from pydantic import BaseModel
from fastapi import Query, Request, HTTPException, Depends
from cat.mad_hatter.decorators import endpoint
from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource

from cat.looking_glass.cheshire_cat import CheshireCat

from cat.looking_glass.stray_cat import StrayCat
from cat.log import log

# from ..types import Agent


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    instructions: Optional[str] = None
    metadata: Optional[dict] = None

class AgentRequestResponse(AgentUpdateRequest):
    id: str = "default"


@endpoint.get(path="/agents", prefix="")
async def list_agents(
    request: Request,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.READ)),
) -> Dict:
    """List all available agents"""
        
    return {
        "agents": list(stray.agents.values())
    }

@endpoint.post(path="/agents", prefix="")
async def create_agent(
    request: Request,
    agent: AgentUpdateRequest,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)),
) -> Dict:
    """Create a new agent"""
    
    new_agent = stray.create_agent(
        name=agent.name or "",
        instructions=agent.instructions or "",
        metadata=agent.metadata or {}
    )
    
    return {
        "success": True,
        "agent": AgentRequestResponse(**new_agent.model_dump())
    }

@endpoint.endpoint(path="/agents/{agent_id}", prefix="", methods=["DELETE"])
async def delete_agent(
    request: Request,
    agent_id: str,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)),
) -> Dict:
    """Delete an existing agent"""
    if agent_id == "default":
        raise HTTPException(
            status_code=400,
            detail={"error": "Cannot delete default agent"}
        )
    
    if agent_id not in stray.agents:
        raise HTTPException(
            status_code=404,
            detail={"error": "Agent not found"}
        )
    
    del stray.agents[agent_id]
    
    return {
        "success": True,
        "message": f"Agent {agent_id} deleted successfully"
    }

@endpoint.get(path="/agents/{agent_id}", prefix="")
async def get_agent(
    request: Request,
    agent_id: str,
    stray: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.READ)),
) -> Dict:
    """Get information about a specific agent"""
    agent = stray.get_agent_by_id(agent_id)
    
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Agent not found"}
        )
    
    return {
        "agent": AgentRequestResponse(**agent.model_dump())
    }

# PATCH collection points metadata
@endpoint.endpoint(path="/agents", methods=["PATCH"], prefix="")
async def update_points_metadata(
    request: Request,
    metadata: AgentUpdateRequest,
    agent_id: str = "default",
    stray: StrayCat=Depends(HTTPAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)),
) -> Dict:
    log.debug(f"User ID: {stray.user_id}")
    log.debug(f"Updating agents: {agent_id}")
    log.debug(f"New agent instructions: {metadata.instructions}")

    agent: Agent = stray.get_agent_by_id(agent_id)

    if agent is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "Agent does not exist."}
        )

    if metadata.name is not None:
        agent.name = metadata.name

    if metadata.instructions is not None:
        agent.instructions = metadata.instructions

    if metadata.metadata is not None:
        agent.metadata = metadata.metadata

    return {
        "success": True,
        "agent": AgentRequestResponse(**agent.model_dump(), id=agent_id)
    }


