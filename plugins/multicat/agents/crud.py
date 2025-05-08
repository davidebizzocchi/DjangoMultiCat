from typing import Dict, Type, Union
from tinydb import Query, TinyDB

from cat.db.database import get_db
from cat.log import log

from cat.plugins.multicat.agents.models import AgentDB
from cat.plugins.multicat.types import Agent

# utils
def cast_agent(payload: Dict):
    if payload is None:
        return None
    
    if not isinstance(payload, Dict):
        return payload
    
    if len(payload.keys()) == 0:
        return None

    return Agent.model_validate(payload)

def from_dict(payload: Dict):
    return AgentDB.model_validate(payload)

def from_agent(payload: Agent):
    return from_dict(payload.model_dump())

def parser(data: Union[str, Agent, AgentDB, Dict], return_type: Type, field="id"):
    if isinstance(data, return_type):
        return data

    # Always cast dict into AgentDB model
    if isinstance(data, Dict):
        data = AgentDB.model_validate(data)

    if isinstance(data, Dict) and (return_type is dict or return_type is Dict):
        return data
    
    # Retrieve the "field" from model
    if isinstance(data, Union[Agent, AgentDB]) and return_type is str:
        result = getattr(data, field, None)
        return result

    # Only Agent to DB, because this is a database (opposite in cast_agent)
    if isinstance(data, Agent) and return_type is AgentDB:
        result = AgentDB.model_validate(data.model_dump())
        return result
    
    return data

class DictWithAgentCast(Dict):
    def cast(self):
        if hasattr(self, "can_cast"):
            if self.can_cast:
                return cast_agent(self)
            
        return self

class AgentManager():
    def __init__(self):
        self.db: TinyDB = get_db()

        self.table = self.db.table("agents")
    
    # decorators
    def parse(input_type: Type = AgentDB, field: str = "id", add_cast: bool = True):
        def wrap(func):
            def ovveride(self, value, *args, **kwargs):
                value = parser(data=value, return_type=input_type, field=field)
                
                result = func(self, value, *args, **kwargs)
                
                if isinstance(result, Dict):
                    result = DictWithAgentCast(result)
                    result.can_cast = add_cast

                    return result
                # If the response is not dict, try cast (is safe)
                else:
                    return cast_agent(result)
            
            return ovveride
        return wrap
    
    def cast_list(add_cast=True):
        def wrap(func):
            def ovveride(self):
                result = func(self)

                if isinstance(result, list):
                    list_ = []
                    for item in result:
                        obj = DictWithAgentCast(item)
                        obj.can_cast = add_cast
                        list_.append(obj)

                    return list_
                
                return result

            return ovveride
        return wrap
    
    @cast_list()
    def list_agents(self):
        return self.table.all()

    @parse(input_type=str)
    def get_agent(self, agent_id: str):
        log.debug(f"Getting agent with id: {agent_id}")
        query = Query()
        agents = self.table.search(query.id == agent_id)

        if len(agents) > 0:
            return agents[0]
        
        return None

    @parse(input_type=AgentDB)
    def create_agent(self, payload: AgentDB, check_if_exists=True):

        if isinstance(payload, Agent):
            payload = AgentDB.model_validate(payload.model_dump())

        # create the agent only if not exists
        if check_if_exists:
            if self.get_agent(payload) is None:
                self.table.insert(payload.model_dump())
        else:
            self.table.insert(payload.model_dump())

        return self.get_agent(payload.id)

    @parse(input_type=AgentDB)
    def update_agent(self, payload: AgentDB):
        query = Query()
        self.table.update(payload.model_dump(), query.id == payload.id)

        return self.get_agent(payload.id)

    @parse(input_type=AgentDB)
    def upsert_agent(self, payload: AgentDB):
        old_agent = self.get_agent(payload.id)

        if old_agent is None:
            self.create_agent(payload)
        else:
            return self.update_agent(payload)
        
        return self.get_agent(payload.id)
    
    @parse(input_type=str, add_cast=False)
    def delete_agent(self, agent_id: str):
        query = Query()
        self.table.remove(query.id == agent_id)

    @parse(input_type=str, add_cast=False)
    def exists(self, agent_id: str):
        return self.get_agent(agent_id) is not None
    
    def all(self):
        return self.list_agents()

manager = AgentManager()
