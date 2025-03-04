from typing import Dict, Union
import uuid

from cat.looking_glass.cheshire_cat import CheshireCat
from cat.log import log

from cat.plugins.multicat.types import Agent
from cat.plugins.multicat.agents.crud import manager as agent_manager


class CommonStrayCat():
    """
    This is the Common StrayCat
    
    - control for agents
    - control for cache with chat_id

    """

    def agents(self):
        return agent_manager.list_agents()

    def get_agent_by_id(self, agent_id):
        return agent_manager.get_agent(agent_id)
    
    def create_agent(self, **kwargs):
        id = kwargs.pop("id", "default")  # "default" mean that not exists!

        # Generate a new agent id if not specified
        if id == "default":
            new_agent_id = str(uuid.uuid4())
        else:
            new_agent_id = id
            agent = self.get_agent_by_id(new_agent_id)

            # If already exists, update the agent
            if agent is not None:
                return agent_manager.update_agent(Agent(id=new_agent_id, **kwargs))

        agent = Agent(id=new_agent_id, **kwargs)
        return agent_manager.create_agent(agent, check_if_exists=False)
    
    def update_agent(self, updated_agent):
        return agent_manager.update_agent(updated_agent)
    
    def delete_agent(self, agent: Union[str, Agent]):
        return agent_manager.delete_agent(agent)
