from typing import Any, Union
from django.db import models
from django.db.models import Q
from django.conf import settings

from cheshire_cat.types import AgentRequest, LLMRequest, Agent as AgentModel
from common.utils import BaseUserModel
from llm.models import LLM


def validate_capabilities(value):
    if not all([capability in settings.CAPABILITIES_TO_PLUGINS.keys() for capability in value]):
        raise ValueError("Invalid capabilities")


class AgentManager(models.Manager):
    def filter(self, *args, **kwargs):
        """Never return the default agent"""
        return super().filter(*args, **kwargs).exclude(agent_id="default")
    
    def filter_include_default(self, *args, **kwargs):
        """Return all agents including the default agent"""
        query = Q(*args, **kwargs) | Q(agent_id="default")
        return super().filter(query)

class Agent(BaseUserModel):
    agent_id = models.CharField(max_length=255, null=True, blank=True, default=None)

    name = models.CharField(max_length=255, default="")
    instructions = models.TextField(default="")
    capabilities = models.JSONField(
        validators=[validate_capabilities],
        default=list
    )
    enable_vector_search = models.BooleanField(default=True, verbose_name="Memory Search")

    llm = models.ForeignKey(LLM, on_delete=models.SET_NULL, null=True, blank=True, related_name="agents")

    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AgentManager()

    class Meta:
        ordering = ("user", "-updated_at")

    def get_agent_kwargs(self, **kwargs):
        metadata = self.metadata.copy()

        metadata["plugins"] = [settings.CAPABILITIES_TO_PLUGINS[cap] for cap in self.capabilities]

        if "metadata" in kwargs:
            metadata.update(kwargs["metadata"])
        if "plugins" in kwargs:
            metadata["plugins"] = kwargs["plugins"]

        agent_kwargs = {
            "id": self.agent_id,
            "name": self.name,
            "instructions": self.instructions,
            "metadata": metadata,
            "enable_vector_search": self.enable_vector_search,
        }

        if self.llm:
            agent_kwargs["llm_name"] = self.llm.name
        elif hasattr(self, 'llm_name') and self.llm_name:
            agent_kwargs["llm_name"] = self.llm_name

        return agent_kwargs
    
    def get_llm_kwargs(self):
        return {
            "name": self.llm.name,
            "llm_class": self.llm.llm_class,
            "config": self.llm.config
        }

    @property
    def agent(self) -> Union[AgentModel, AgentRequest]:
        if self.agent_id is None:
            return AgentRequest.model_validate(self.get_agent_kwargs())
        else:
            return AgentModel.model_validate(self.get_agent_kwargs())

    def model_dump(self) -> dict[str, Any]:
        return self.agent.model_dump()
        
    def full_model_dump(self) -> AgentModel:
        return AgentModel.model_validate(self.get_agent_kwargs()).model_dump()
    
    @property
    def llm_model_instance(self) -> LLMRequest:
        llm_kwargs = self.get_llm_kwargs()
        if llm_kwargs is None:
            return None
        return LLMRequest.model_validate(llm_kwargs)
    
    def llm_dump(self) -> LLMRequest:
        llm_model = self.llm_model_instance
        if llm_model:
            return llm_model.model_dump()
        return None
    
    @staticmethod
    def get_default():
        from users.models import UserProfile
        return Agent.objects.get_or_create(agent_id="default", user=UserProfile.get_admin().user)[0]
    
    @property
    def is_default(self):
        return self.agent_id == "default"
    
    def create_agent(self, save=True):
        if self.is_default:
            return self.agent
        
        agent = self.client.create_agent(self)
        self.agent_id = agent.id

        if save:
            self.save(update_fields=["agent_id"])

        return agent

    def save(self, *args, **kwargs):
        if self.is_default:
            self.name = "Default"

        super().save(*args, **kwargs)

        if self.agent_id is None:
            self.create_agent()
        elif self.pk and not self.is_default:
            self.client.update_agent(self)

        llm_instance = self.llm_model_instance
        if llm_instance:
            self.client.update_llm(llm_instance)

    def delete(self, *args, **kwargs):
        self.client.delete_agent(self.agent_id)
        
        return super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.agent_id})"
