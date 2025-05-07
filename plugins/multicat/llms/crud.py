
from typing import Dict
from tinydb import Query, TinyDB

from cat.db.database import get_db
from cat.factory.llm import get_llm_from_name

from cat.plugins.multicat.llms.models import LLMModel
from cat.plugins.multicat.types import LLM


class LLMManager:
    def __init__(self):
        self.db: TinyDB = get_db()

        self.table = self.db.table("llms")
        
    def _cast(self, payload: Dict):
        if payload is None:
            return None
        return LLM.model_validate(payload)
    
    def _validate(self, payload, **kwargs):
        result = None
        if isinstance(payload, Dict):
            result = LLMModel.model_validate(kwargs)

            result.config = payload

        if isinstance(payload, LLM):
            result = LLMModel.model_validate(payload.model_dump())

        return result or payload

    def _cast_llm_settings(self, payload: LLMModel):
        if isinstance(payload, Dict):
            payload = self._cast(payload)

        llm_class = get_llm_from_name(payload.llm_class)

        if llm_class is None:
            raise ValueError(f"LLM class {payload.llm_class} not found")

        return llm_class.get_llm_from_config(payload.config)


    def list(self, cast=False):
        results = []
        for payload in self.table.all():
            results.append(self._cast(payload) if not cast else self._cast_llm_settings(payload))

        return results
    
    def create(self, payload: LLMModel, **kwargs):
        payload = self._validate(payload, **kwargs)

        if isinstance(payload, LLMModel):
            self.table.insert(payload.model_dump())

        return self.get(payload.name)

    def update(self, payload: LLMModel, **kwargs):
        payload = self._validate(payload, **kwargs)

        query = Query()
        self.table.update(payload, query.name == payload.name)

        return self.get(payload.name)

    def upsert(self, payload: LLMModel, **kwargs):
        payload = self._validate(payload, **kwargs)
        
        old_llm = self.get(payload.name)

        if old_llm is None:
            self.create(payload)
        else:
            return self.update(payload)
        
        return self.get(payload.name)
    
    def get(self, name: str, cast=False):
        query = Query()
        result = self._cast(self.table.get(query.name == name))

        if result is None:
            return None

        if cast:
            return self._cast_llm_settings(result)

        return result

    def delete(self, llm_name: str):
        query = Query()
        self.table.remove(query.name == llm_name)

    def exists(self, llm_name: str):
        return self.get(llm_name) is not None
    
    def all(self):
        return self.list()

manager = LLMManager()

