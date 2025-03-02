from typing import Dict
import uuid

from cat.plugins.multicat.types import Agent
from cat.looking_glass.cheshire_cat import CheshireCat


class CommonStrayCat():
    """
    This is the Common StrayCat
    
    - control for agents
    - control for cache with chat_id

    """

    def get_agent_by_id(self, agent_id):
        if agent_id in self.agents:
            return self.agents[agent_id]
        
        return None
    
    @property
    def agents(self) -> Dict[str, Agent]:
        return CheshireCat().agents
    
    def create_agent(self, **kwargs):
        id = kwargs.pop("id", "default")

        # Generate a new agent id if not specified
        if id == "default":
            new_agent_id = str(uuid.uuid4())
        else:
            new_agent_id = id

            # If already exists, update the agent
            if new_agent_id in self.agents:
                self.agents[new_agent_id] = Agent(id=new_agent_id, **kwargs)
                return self.agents[new_agent_id]

        # Check if the agent already exists
        while new_agent_id in self.agents:
            new_agent_id = str(uuid.uuid4())

        agent = Agent(id=new_agent_id, **kwargs)
        self.agents[new_agent_id] = agent

        return agent
