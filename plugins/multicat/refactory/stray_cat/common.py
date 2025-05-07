from typing import Union
import uuid

from cat.looking_glass.cheshire_cat import CheshireCat

from cat.plugins.multicat.types import Agent, LLM

from cat.plugins.multicat.agents.crud import manager as agent_manager
from cat.plugins.multicat.llms.crud import manager as llm_manager

from cat.plugins.multicat.llms.models import LLMModel
from cat.plugins.multicat.settings import MultiCatSettings


class CommonStrayCat():
    """
    This is the Common StrayCat
    
    - control for agents
    - control for cache with chat_id

    """

    @property
    def settings(self) -> MultiCatSettings:
        return MultiCatSettings.model_validate(self.mad_hatter.get_plugin().load_settings())


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

    # LLM
    def llms(self, cast=True):
        return llm_manager.list_llms(cast=cast)
    
    def get_llm_by_name(self, name, database_only=False, save=False, cast=False):
        cat = CheshireCat()

        if not hasattr(cat, "llms"):
            cat.llms = {}

        if not database_only and name in cat.llms:
            return cat.llms[name]

        llm = llm_manager.get(name, cast=cast)

        if save:
            cat.llms[name] = llm

        return llm
    
    def create_llm(self, **kwargs):
        llm = LLMModel.model_validate(kwargs)
        return llm_manager.create(llm)
    
    def update_llm(self, updated_llm):
        return llm_manager.update(updated_llm)
    
    def delete_llm(self, llm: Union[str, LLMModel]):
        if isinstance(llm, str):
            llm = llm_manager.delete(llm)

        if isinstance(llm, LLMModel):
            return llm_manager.delete(llm.name)
        
        return ValueError("Invalid LLM type. Must be str or LLMModel.")

    def upsert_llm(self, llm: Union[LLMModel, LLM] = None, **kwargs):

        if llm is None:
            config = kwargs.pop("config", kwargs)
            return llm_manager.upsert(config, **kwargs)
        
        return llm_manager.upsert(llm, **kwargs)

    # Files
    def get_file_list(self):
        return self.memory.vectors.collections["declarative"].get_all_file_names(self.chat_id if self.chat_id != "default" else None)