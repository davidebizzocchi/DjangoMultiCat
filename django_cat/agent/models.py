from typing import Any, Union
from django.db import models
from django.dispatch import receiver
from cheshire_cat.types import AgentRequest, Agent as AgentModel
from common.utils import BaseUserModel

from app.signals import server_start

from icecream import ic


class AgentManager(models.Manager):
    def filter(self, *args, **kwargs):
        """Never return the default agent"""
        return super().filter(*args, **kwargs).exclude(agent_id="default")

class Agent(BaseUserModel):
    agent_id = models.CharField(max_length=255, null=True, blank=True, default=None)
    name = models.CharField(max_length=255, default="")
    instructions = models.TextField(default="")
    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AgentManager()

    class Meta:
        ordering = ("user", "-updated_at")


    @property
    def agent(self) -> Union[AgentModel, AgentRequest]:
        if self.agent_id is None:
            return AgentRequest(
                name=self.name,
                instructions=self.instructions,
                metadata=self.metadata
            )
        else:
            return AgentModel(
                id=self.agent_id,
                name=self.name,
                instructions=self.instructions,
                metadata=self.metadata
            )
        
    def model_dump(self) -> dict[str, Any]:
        return self.agent.model_dump()
        
    def full_model_dump(self) -> AgentModel:
        return AgentModel(
            id=self.agent_id,
            name=self.name,
            instructions=self.instructions,
            metadata=self.metadata
        ).model_dump()
    
    @staticmethod
    def get_default():
        from users.models import UserProfile
        return Agent.objects.get_or_create(agent_id="default", user=UserProfile.get_admin().user)[0]
    
    @property
    def is_default(self):
        return self.agent_id == "default"
    
    def create_agent(self, save=True):
        # If is default, is not necessary to create an agent
        if self.is_default:
            return self.agent
        
        agent = self.client.create_agent(self)
        self.agent_id = agent.id

        if save:
            self.save(update_fields=["agent_id"])

        return agent

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.agent_id is None:
            self.create_agent()
        elif self.pk and not self.is_default:
            self.client.update_agent(self)

    def delete(self, *args, **kwargs):
        self.client.delete_agent(self.agent_id)
        
        return super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.agent_id})"
    
@receiver(server_start)
def create_agents_on_server_start(sender, **kwargs):
    for agent in Agent.objects.all():
        agent.create_agent()
    
    ic("Agents created on server start")